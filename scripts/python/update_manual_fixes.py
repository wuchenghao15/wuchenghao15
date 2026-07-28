#!/usr/bin/env python3
import os
import ast
import sqlite3

files_to_update = [
    'education_brain_science_service.py',
    'service_manager.py',
    'app/unified_rule_manager.py',
    'security_vulnerability_service.py'
]

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

updated_count = 0

for file_name in files_to_update:
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    
    if not os.path.exists(file_path):
        print(f'❌ 文件不存在: {file_path}')
        continue
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            
            cursor.execute('''
                SELECT COUNT(*) FROM syntax_repair_logs WHERE file_path = ? AND fix_status = "failed"
            ''', (file_path,))
            
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute('''
                    UPDATE syntax_repair_logs SET 
                        after_content = ?, 
                        fix_status = "success",
                        verified = 1
                    WHERE file_path = ? AND fix_status = "failed"
                ''', (content, file_path))
                
                cursor.execute('''
                    UPDATE syntax_errors SET status = "fixed" 
                    WHERE file_path = ? AND status = "error"
                ''', (file_path,))
                
                conn.commit()
                updated_count += 1
                print(f'✅ 更新成功: {file_path}')
            else:
                print(f'ℹ️ 无需更新(已成功): {file_path}')
                
        except SyntaxError as e:
            print(f'❌ 仍有语法错误: {file_path} - {e}')
            
    except Exception as e:
        print(f'❌ 读取失败: {file_path} - {e}')

conn.commit()
conn.close()

print(f'\n更新完成，共更新 {updated_count} 个文件')
