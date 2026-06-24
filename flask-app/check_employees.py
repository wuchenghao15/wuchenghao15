import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# 查看ai_employees主表
print('=== ai_employees主表所有记录 ===')
cursor.execute("SELECT * FROM ai_employees")
for row in cursor.fetchall():
    print(f'  {row}')

# 查看ai_employee_module涉及到的employee_id
print()
print('=== ai_employee_module涉及的employee_id ===')
cursor.execute("SELECT DISTINCT employee_id FROM ai_employee_module ORDER BY employee_id")
for row in cursor.fetchall():
    print(f'  {row[0]}')

# 查看ai_specialized_skills涉及的employee_id
print()
print('=== ai_specialized_skills涉及的employee_id ===')
cursor.execute("SELECT DISTINCT employee_id FROM ai_specialized_skills ORDER BY employee_id")
for row in cursor.fetchall():
    print(f'  {row[0]}')

conn.close()