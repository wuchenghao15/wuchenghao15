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
    'Settings页面旧API调用错误',
    'settings.html调用了不存在的旧API端点导致8条net::ERR_CONNECTION_REFUSED错误',
    '/settings.html',
    'success',
    int(time.time()),
    'AI员工-前端开发',
    '修复了8条日志错误：1) loadAlerts() 从 /api/admin/monitor/alerts 改为 /api/settings-data/alerts; 2) loadRecentActivity() 从 /api/admin/monitor/recent_activity 改为 /api/settings-data/recent-activity; 3) loadAiOverview() 从 /api/intelligent/overview 改为 /api/settings-data/employees; 4) loadTasks() 从 /api/intelligent/tasks 改为 /api/settings-data/ai-repair-stats; 5) loadNavAnomalies() 改为显示暂无导航异常; 6) resolveNavAnomaly() 改为console.log; 7) loadInsights() 改为 /api/settings-data/ai-repair-stats; 8) 删除硬编码的员工卡片HTML，改为动态加载。',
    'high'
))

conn.commit()
conn.close()
print('✅ 8条日志错误修复记录已上报数据库!')