#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化学生行为管理系统的数据库表
直接使用SQL，不依赖Flask应用
"""

import sqlite3
import os

def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    
    print(f"连接数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建行为分类表
        print("创建行为分类表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                points_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # 创建行为记录表
        print("创建行为记录表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                behavior_type TEXT NOT NULL CHECK (behavior_type IN ('positive', 'negative')),
                points INTEGER DEFAULT 0,
                description TEXT,
                recorded_by INTEGER,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES behavior_categories(id),
                FOREIGN KEY (recorded_by) REFERENCES users(id)
            )
        ''')
        
        # 创建行为目标表
        print("创建行为目标表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                category_id INTEGER,
                target_points INTEGER NOT NULL,
                current_points INTEGER DEFAULT 0,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'expired')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES behavior_categories(id)
            )
        ''')
        
        # 插入默认分类（如果不存在）
        print("插入默认分类...")
        default_categories = [
            ("课堂表现", "课堂参与度、注意力集中", 5),
            ("作业完成", "按时完成作业情况", 3),
            ("考试成绩", "考试成绩表现", 10),
            ("纪律表现", "遵守纪律情况", 5),
            ("团队合作", "小组合作表现", 4),
            ("创新实践", "创新思维与实践", 8),
            ("助人为乐", "帮助同学、公益活动", 6),
            ("出勤情况", "按时到校、不迟到早退", 3),
            ("学习态度", "学习积极性、主动性", 4),
            ("其他", "其他行为表现", 2)
        ]
        
        for name, description, points in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO behavior_categories (name, description, points_default)
                VALUES (?, ?, ?)
            ''', (name, description, points))
        
        conn.commit()
        print("\n✓ 数据库初始化成功！")
        print("\n创建的表：")
        print("  - behavior_categories (行为分类表)")
        print("  - behavior_records (行为记录表)")
        print("  - behavior_goals (行为目标表)")
        print("\n默认分类：")
        for i, (name, desc, points) in enumerate(default_categories, 1):
            print(f"  {i}. {name} - {desc} (默认{points}分)")
            
        # 验证数据是否插入成功
        cursor.execute("SELECT COUNT(*) FROM behavior_categories")
        count = cursor.fetchone()[0]
        print(f"\n当前分类数: {count}")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    main()
