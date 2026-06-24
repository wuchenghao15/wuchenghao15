import sqlite3
import json

db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/mtscos.db'

rules = {
    'PERM_VIEW_DASHBOARD': ['student', 'designer', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    'PERM_VIEW_SETTINGS': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    'PERM_MANAGE_USERS': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    'PERM_DELETE_USER': ['super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    'PERM_MANAGE_DATABASE': ['super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    'PERM_VIEW_LOGS': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
}

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    for code, roles in rules.items():
        value = json.dumps(roles)
        cursor.execute('UPDATE system_rules SET rule_value = ? WHERE rule_code = ?', (value, code))
        print(f'Updated {code}: {value}')
    conn.commit()

print('All rules updated successfully')