import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# 检查核心规则表
tables = ['system_rules', 'rule_groups', 'access_control_rules', 'rule_constraints']
for table in tables:
    print(f'=== {table} ===')
    cursor.execute(f'PRAGMA table_info({table})')
    for row in cursor.fetchall():
        print(f'  {row}')

    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    print(f'  行数: {cursor.fetchone()[0]}')

    cursor.execute(f'SELECT * FROM {table} LIMIT 3')
    print('  示例数据:')
    for row in cursor.fetchall():
        print(f'    {row}')
    print()
conn.close()