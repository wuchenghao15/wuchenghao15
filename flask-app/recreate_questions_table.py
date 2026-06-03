# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from app.utils.db import db_manager

# 重新创建questions表
table_name = 'questions'

# 定义表结构
columns = {
    'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
    'question_id': 'TEXT',
    'question_text': 'TEXT NOT NULL',
    'question_type': 'TEXT',
    'difficulty': 'TEXT',
    'options': 'TEXT',
    'correct_answer': 'TEXT',
    'explanation': 'TEXT',
    'tags': 'TEXT',
    'status': 'TEXT',
    'created_at': 'TEXT',
    'updated_at': 'TEXT'
}

# 创建表
success = db_manager.create_table(table_name, columns)
if success:
    print(f"表 {table_name} 创建成功")
else:
    print(f"表 {table_name} 创建失败")
