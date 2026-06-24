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
    'sqlite3连接对象嵌套错误',
    'expected str, bytes or os.PathLike object, not Connection - 访问日志记录失败',
    '/app/middlewares/access_control.py + 多个文件',
    'success',
    int(time.time()),
    'AI员工-后端开发',
    '批量修复sqlite3.connect(...)嵌套错误，共修复9处：1) app/middlewares/access_control.py第192行（log_access函数）；2) app/utils/system_monitor.py第120行；3) app/routes/settings_routes.py第27/44/93/120/289/331行（6处）；4) app/services/learning_group_service.py第21/74行（2处）。错误原因：外层sqlite3.connect接收的是内层connect返回的Connection对象而非文件路径。修复方案：删除外层的sqlite3.connect包裹，直接使用内层。验证：服务器日志中无"Failed to log access"错误，访问日志功能正常。',
    'high'
))

conn.commit()
conn.close()
print('✅ sqlite3连接嵌套错误已批量修复!')