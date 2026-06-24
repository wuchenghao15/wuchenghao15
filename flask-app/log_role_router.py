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
    '角色路由跳转规则系统',
    '登录后无角色差异化跳转，需要根据组别自动跳转至对应页面',
    '/app/utils/role_router.py + /app/api/auth_api.py + /app.py + /src/html/index.html',
    'success',
    int(time.time()),
    'AI员工-系统架构',
    '创建角色路由跳转规则系统：1) 创建RoleRouter类管理角色跳转规则，定义9个角色的跳转路径和侧边栏菜单；2) 修改登录API返回redirect路径和sidebar_items；3) 更新前端登录处理逻辑使用后端返回的跳转路径；4) 在app.py中添加角色路由：/exam(学生/教师/研究员/管理员)、/arduino(设计师)、/teacher(教师)、/researcher(教研员)、/dashboard(重定向到角色页面)；5) 不同管理员级别显示不同设置页面权限：admin显示3个菜单，super_admin显示5个，hardware_admin显示6个。',
    'high'
))

conn.commit()
conn.close()
print('✅ 角色路由跳转规则系统已部署!')