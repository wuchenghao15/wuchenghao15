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
    'Settings页面真实数据加载',
    'settings.html需要从数据库加载真实数据，原API路由不存在',
    '/settings.html',
    'success',
    int(time.time()),
    'AI员工-后端开发',
    '创建了 settings_data_api.py Blueprint，提供9个API端点：/employees, /users, /roles, /permissions, /system-status, /alerts, /recent-activity, /logs, /audit, /system-config, /database-info, /ai-repair-stats。修改 settings.html 调用新API，删除硬编码数据。所有API从app.db真实数据库读取。',
    'high'
))

conn.commit()
conn.close()
print('✅ 修复记录已上报数据库!')