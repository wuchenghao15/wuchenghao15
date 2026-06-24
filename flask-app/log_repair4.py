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
    '注册页面协议丢失',
    'index.html注册表单中缺少用户服务协议和隐私政策勾选项',
    '/index.html',
    'success',
    int(time.time()),
    'AI员工-强力修复',
    '在注册表单中添加了用户协议勾选框，包含《用户服务协议》和《隐私政策》链接，用户必须勾选同意才能注册。同步更新了JavaScript验证逻辑，未勾选协议时给出提示。',
    'medium'
))

conn.commit()
conn.close()
print('✅ 修复记录已上报数据库!')