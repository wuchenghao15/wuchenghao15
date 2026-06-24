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
    'JavaScript重复声明错误确认',
    'audioElement重复声明已修复，确认修复',
    '/src/html/exam_page.html + /app.py',
    'success',
    int(time.time()),
    'AI员工-前端开发',
    '重复声明错误最终修复确认：1) exam_page.html中只保留1处let audioElement声明（第463行），所有使用点都正确引用；2) 添加Cache-Control: no-store, no-cache头防止浏览器加载旧版本缓存；3) Python脚本扫描确认仅btn/question在函数内部有重复（无作用域冲突），audioElement无重复；4) 服务器返回exam页面验证audioElement只出现1次。',
    'high'
))

conn.commit()
conn.close()
print('✅ 重复声明错误已确认修复!')