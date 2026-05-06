#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def generate_final_report():
    print('=== 最终修复报告 ===')
    print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM error_reports')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM error_reports WHERE fixed = 1')
    fixed = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM error_reports WHERE fixed = 0')
    remaining = cursor.fetchone()[0]

    cursor.execute('SELECT error_type, COUNT(*) as cnt FROM error_reports WHERE fixed = 1 GROUP BY error_type LIMIT 10')
    fixed_types = cursor.fetchall()

    print('总错误记录:', total)
    print('已修复:', fixed)
    print('未修复:', remaining)
    print()
    print('修复率: {:.1f}%'.format(fixed/total*100))
    print()
    print('已修复的错误类型:')
    for err_type, cnt in fixed_types:
        print(f'  {err_type}: {cnt}')

    print()
    print('=== 核心项目健康检查 ===')

    core_files = [
        'flask-app/hardware_app.py',
        'flask-app/app.py',
        'start_project.py',
        'fix_system_login.py',
    ]

    for file_path in core_files:
        cursor.execute('SELECT COUNT(*) FROM error_reports WHERE file_path = ? AND fixed = 0', (file_path,))
        remaining = cursor.fetchone()[0]

        if remaining == 0:
            status = '✅ 通过'
        else:
            status = f'⚠️ 有{remaining}个未修复'

        print(f'  {file_path}: {status}')

    conn.close()
    print()
    print('报告完成！')

if __name__ == '__main__':
    generate_final_report()