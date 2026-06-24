import sqlite3
import uuid
import time

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

cursor.execute('''
    INSERT INTO ai_repair_logs (repair_id, error_type, error_message, file_path, fix_status, repair_time, applied_by, details, severity)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    str(uuid.uuid4()),
    'HTML合并冲突',
    'index.html存在git合并冲突标记导致SyntaxError: Unexpected token \'===\'',
    '/index.html',
    'success',
    int(time.time()),
    'AI员工-强力修复',
    '修复了index.html中的git合并冲突标记，重写整个文件',
    'high'
))

conn.commit()
conn.close()
print('✅ 修复记录已上报数据库!')