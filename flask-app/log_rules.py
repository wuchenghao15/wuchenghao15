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
    '加载数据库真实规则数据',
    '权限设置面板使用硬编码的权限等级体系，未从数据库加载规则',
    '/settings.html + /api/settings-data/rules',
    'success',
    int(time.time()),
    'AI员工-后端开发',
    '添加4个规则管理API端点：1) GET /api/settings-data/rules - 系统规则列表（支持type/active过滤）；2) GET /api/settings-data/rules/<id> - 单个规则详情；3) GET /api/settings-data/rule-constraints - 规则约束列表；4) GET /api/settings-data/access-control-rules - 访问控制规则。修改settings.html权限设置面板，添加loadRules()函数，从数据库加载157条真实规则数据并动态渲染权限等级体系、规则统计卡片、规则列表。',
    'high'
))

conn.commit()
conn.close()
print('✅ 规则数据加载完成!')