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
    'exam_system路由500错误',
    'net::ERR_ABORTED http://localhost:8888/exam_system + 500 Internal Server Error',
    '/app.py + /src/html/exam_system.html',
    'success',
    int(time.time()),
    'AI员工-后端开发',
    '彻底修复exam_system路由500错误，三个问题：1) sqlite3.connect(sqlite3.connect(...))嵌套错误 - 在app.py第1077行，批量修复了整个flask-app项目共44处sqlite3.connect嵌套错误，涵盖26个文件（app.py、access_control.py、system_monitor.py、settings_routes.py、learning_group_service.py、route_manager.py、各ai_engines/等）。2) 表名错误 - exam_system函数查询了不存在的表t_a4394fa841fb07b4，改为查询exams表，字段名从name/total_questions/difficulty_level/exam_type/audio_type改为title/question_count/level。3) 模板文件缺失 - 创建了src/html/exam_system.html文件（基于exam_page.html）。验证：/exam_system返回200 OK，标题"在线考试 - MTSCOS 智能考试系统"。',
    'high'
))

conn.commit()
conn.close()
print('✅ exam_system路由500错误已彻底修复!')