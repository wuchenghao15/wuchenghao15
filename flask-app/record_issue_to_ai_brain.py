#!/usr/bin/env python3
"""
将HTML标签显示问题记录到AI脑库特征库
用于AI学习升级，提供问题特征和解决方案
"""

import os
import sqlite3
import json
from datetime import datetime

# 获取数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dev.db')

def connect_db():
    """连接到SQLite数据库"""
    return sqlite3.connect(db_path)

def create_table(conn):
    """创建AI脑库特征表（如果不存在）"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_brain_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_type TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            issue_characteristics TEXT NOT NULL,
            solution TEXT NOT NULL,
            severity INTEGER NOT NULL,
            impact_scope TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()

def record_issue(conn):
    """记录span标签显示不全问题到AI脑库特征库"""
    cursor = conn.cursor()
    
    # 问题特征
    feature_type = "HTML_DISPLAY"
    issue_description = "span标签文本显示不全"
    issue_characteristics = json.dumps({
        "element": "span",
        "class_names": ["text-sm", "text-gray-600", "hover:text-indigo-600", "transition-colors"],
        "text_content": "记住我",
        "problem": "文本显示不全",
        "trigger": "标签宽度不足",
        "context": "登录页面的'记住我'复选框文本",
        "browser": "all"
    })
    solution = json.dumps({
        "type": "CSS_STYLE_ADJUSTMENT",
        "changes": [
            {"property": "min-width", "value": "60px", "reason": "确保标签有足够宽度显示文本"},
            {"property": "whitespace", "value": "nowrap", "reason": "防止文本换行"},
            {"property": "margin-left", "value": "2px", "reason": "调整间距，确保文本完整显示"}
        ],
        "implementation": "直接在span标签中添加内联样式或修改CSS类"
    })
    severity = 1  # 1: 轻微, 2: 中等, 3: 严重
    impact_scope = "FRONTEND_DISPLAY"
    created_at = datetime.utcnow().isoformat()
    updated_at = datetime.utcnow().isoformat()
    
    # 插入记录
    cursor.execute('''
        INSERT INTO ai_brain_features 
        (feature_type, issue_description, issue_characteristics, solution, severity, impact_scope, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        feature_type, 
        issue_description, 
        issue_characteristics, 
        solution, 
        severity, 
        impact_scope, 
        created_at, 
        updated_at
    ))
    
    conn.commit()
    print(f"问题特征已成功记录到AI脑库特征库，记录ID: {cursor.lastrowid}")

def main():
    """主函数"""
    try:
        # 连接数据库
        conn = connect_db()
        print(f"成功连接到数据库: {db_path}")
        
        # 创建表
        create_table(conn)
        print("AI脑库特征表检查/创建完成")
        
        # 记录问题
        record_issue(conn)
        
        # 关闭连接
        conn.close()
        print("数据库连接已关闭")
        
    except Exception as e:
        print(f"记录问题到AI脑库特征库失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
