#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库迁移脚本 - 添加formula_type和derivation_steps列"""
import sqlite3
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def migrate_database():
    """执行数据库迁移"""
    db_path = os.path.join(project_root, 'app.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='math_formulas'")
        if not cursor.fetchone():
            print("math_formulas表不存在，无需迁移")
            return True
        
        # 获取现有列信息
        cursor.execute("PRAGMA table_info(math_formulas)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        print(f"现有列: {existing_columns}")
        
        # 添加formula_type列
        if 'formula_type' not in existing_columns:
            print("添加formula_type列...")
            cursor.execute("ALTER TABLE math_formulas ADD COLUMN formula_type TEXT DEFAULT 'basic'")
            print("✓ formula_type列添加成功")
        else:
            print("formula_type列已存在")
        
        # 添加derivation_steps列
        if 'derivation_steps' not in existing_columns:
            print("添加derivation_steps列...")
            cursor.execute("ALTER TABLE math_formulas ADD COLUMN derivation_steps TEXT")
            print("✓ derivation_steps列添加成功")
        else:
            print("derivation_steps列已存在")
        
        conn.commit()
        print("\n数据库迁移完成!")
        
        # 验证迁移结果
        cursor.execute("PRAGMA table_info(math_formulas)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"最终列: {final_columns}")
        
        return True
        
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
