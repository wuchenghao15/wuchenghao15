import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# 查看ai_employees表结构
print('=== ai_employees表结构 ===')
cursor.execute("PRAGMA table_info(ai_employees)")
for row in cursor.fetchall():
    print(f'  {row}')

print()
print('=== ai_employees所有记录 ===')
cursor.execute("SELECT * FROM ai_employees")
for row in cursor.fetchall():
    print(f'  {row}')

print()
print('=== ai_employee_tasks表结构 ===')
cursor.execute("PRAGMA table_info(ai_employee_tasks)")
for row in cursor.fetchall():
    print(f'  {row}')

print()
print('=== ai_employee_tasks所有记录 ===')
cursor.execute("SELECT * FROM ai_employee_tasks")
for row in cursor.fetchall():
    print(f'  {row}')

print()
print('=== ai_employee_module表结构 ===')
cursor.execute("PRAGMA table_info(ai_employee_module)")
for row in cursor.fetchall():
    print(f'  {row}')

print()
print('=== ai_employee_module所有记录 ===')
cursor.execute("SELECT * FROM ai_employee_module")
for row in cursor.fetchall():
    print(f'  {row}')

print()
print('=== ai_specialized_skills表结构 ===')
cursor.execute("PRAGMA table_info(ai_specialized_skills)")
for row in cursor.fetchall():
    print(f'  {row}')

print()
print('=== ai_specialized_skills所有记录 ===')
cursor.execute("SELECT * FROM ai_specialized_skills")
for row in cursor.fetchall():
    print(f'  {row}')

conn.close()