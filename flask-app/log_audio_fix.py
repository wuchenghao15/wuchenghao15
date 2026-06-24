import sqlite3
import uuid
import time

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO ai_repair_logs
    (repair_id, error_type, error_message, file_path, fix_status, repair_time, applied_by, details, severity)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    str(uuid.uuid4()),
    'JavaScript重复声明错误',
    'exam_page.html中audioElement变量被重复声明两次',
    '/src/html/exam_page.html',
    'success',
    int(time.time()),
    'AI员工-前端开发',
    '修复SyntaxError: Identifier audioElement has already been declared错误。问题：第463行和第660行都使用let声明了audioElement。修复：删除第660行的重复声明let audioElement = null，保留第463行的声明。已通过node -c语法验证。',
    'high'
))

conn.commit()
conn.close()
print('✅ 重复声明错误已修复!')