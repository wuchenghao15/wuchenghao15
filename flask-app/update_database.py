#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('data/mtscos_ai_project.db')
cursor = conn.cursor()

# 1. 为用户表添加头像字段
print("为用户表添加头像字段...")
try:
    cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT;")
    conn.commit()
    print("用户表添加头像字段成功")
except Exception as e:
    if "duplicate column name" in str(e):
        print("用户表已经存在头像字段")
    else:
        print(f"添加头像字段时出错: {e}")

# 2. 创建项目历史表
print("\n创建项目历史表...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        description TEXT,
        project_id TEXT,
        project_name TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
except Exception as e:
    print(f"创建项目历史表时出错: {e}")
# 3. 检查修改后的用户表结构
print("\n修改后的用户表结构:")
    cursor.execute('PRAGMA table_info(users)')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
except Exception as e:
    print(f"错误: {e}")

print("\n项目历史表结构:")
    cursor.execute('PRAGMA table_info(project_history)')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
except Exception as e:
    print(f"错误: {e}")

