#!/usr/bin/env python3
import sqlite3
import os
import ast

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/mtscos.db'

conn = sqlite3.connect(DATABASE_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT file_path, before_content, after_content FROM syntax_repair_logs WHERE fix_status = 'success'")
results = cursor.fetchall()

print("=== 审计成功修复的文件 ===\n")
print(f"待审计文件数: {len(results)}\n")

corrupted_count = 0
ok_count = 0
missing_count = 0

for row in results:
    file_path = row['file_path']
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        missing_count += 1
        continue
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        try:
            ast.parse(current_content)
            ok_count += 1
        except SyntaxError as e:
            print(f"❌ 文件已损坏: {file_path}")
            print(f"   错误: {e}")
            corrupted_count += 1
            
    except Exception as e:
        print(f"❌ 读取失败: {file_path} - {e}")
        corrupted_count += 1

print(f"\n审计结果:")
print(f"  ✓ 通过: {ok_count}")
print(f"  ❌ 已损坏: {corrupted_count}")
print(f"  ⚠️ 不存在: {missing_count}")

if corrupted_count > 0:
    print(f"\n警告: 有 {corrupted_count} 个文件修复后仍有语法错误!")

conn.close()
