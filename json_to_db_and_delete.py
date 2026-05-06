#!/usr/bin/env python3
"""
上传所有JSON数据到数据库并删除本地JSON文件
"""

import os
import json
import sqlite3
from datetime import datetime

def find_json_files(root_dir):
    """查找所有JSON文件"""
    exclude_dirs = ['venv', '__pycache__', '.git', 'node_modules']
    json_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            if filename.endswith('.json'):
                json_files.append(os.path.join(dirpath, filename))
    return json_files

def create_db_tables(conn):
    """创建JSON数据存储表"""
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS json_backup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            data_size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            backed_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()

def backup_json_to_db(file_path, conn):
    """备份单个JSON文件到数据库"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证JSON格式
        try:
            json_data = json.loads(content)
        except json.JSONDecodeError:
            print(f"  ⚠️  {file_path} - 无效JSON格式，跳过")
            return False
        
        data_size = len(content)
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO json_backup (file_path, content, data_size, backed_up_at)
            VALUES (?, ?, ?, ?)
        ''', (file_path, content, data_size, datetime.now().isoformat()))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"  ❌ {file_path} - 备份失败: {str(e)}")
        return False

def delete_json_file(file_path):
    """删除JSON文件"""
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        print(f"  ❌ 删除失败 {file_path}: {str(e)}")
        return False

def main():
    project_root = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
    
    print("=== 上传JSON数据到数据库并删除本地JSON文件 ===")
    print(f"项目根目录: {project_root}\n")

    # 查找所有JSON文件
    json_files = find_json_files(project_root)
    print(f"找到 {len(json_files)} 个JSON文件")

    if not json_files:
        print("没有找到JSON文件，任务完成")
        return

    # 连接数据库
    db_path = os.path.join(project_root, 'flask-app', 'app.db')
    conn = sqlite3.connect(db_path)
    
    # 创建表
    create_db_tables(conn)
    
    # 备份JSON文件到数据库
    print("\n开始备份JSON文件到数据库...")
    backup_success = 0
    backup_failed = 0
    
    for file_path in json_files:
        print(f"  处理: {file_path}")
        if backup_json_to_db(file_path, conn):
            backup_success += 1
        else:
            backup_failed += 1
    
    print(f"\n备份完成: 成功 {backup_success} 个, 失败 {backup_failed} 个")

    # 删除本地JSON文件
    print("\n开始删除本地JSON文件...")
    delete_success = 0
    delete_failed = 0
    
    for file_path in json_files:
        if delete_json_file(file_path):
            delete_success += 1
        else:
            delete_failed += 1
    
    print(f"删除完成: 成功 {delete_success} 个, 失败 {delete_failed} 个")
    
    conn.close()
    
    print("\n=== 任务完成 ===")
    print(f"已备份到数据库: {backup_success} 个文件")
    print(f"已删除本地文件: {delete_success} 个文件")
    print(f"数据库位置: {db_path}")

if __name__ == '__main__':
    main()