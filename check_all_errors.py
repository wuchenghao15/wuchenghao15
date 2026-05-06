#!/usr/bin/env python3
import sqlite3
import subprocess
import os
import ast
from datetime import datetime

def report_error(error_type, message, file_path=None, line_number=None, fixed=False, fix_desc=None):
    try:
        conn = sqlite3.connect('flask-app/app.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO error_reports 
            (error_type, error_message, file_path, line_number, timestamp, fixed, fix_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (error_type, message, file_path, line_number, datetime.now().isoformat(), 
              1 if fixed else 0, fix_desc))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'上报失败: {e}')

def check_syntax(file_path):
    errors = []
    if not os.path.exists(file_path):
        return errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
    except SyntaxError as e:
        errors.append({
            'type': 'SyntaxError',
            'message': str(e),
            'file': file_path,
            'line': e.lineno
        })
    except Exception as e:
        errors.append({
            'type': 'ParseError',
            'message': str(e),
            'file': file_path
        })
    
    return errors

def check_all_files():
    errors = []
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    python_files = []
    for root, dirs, files in os.walk(project_dir):
        for f in files:
            if f.endswith('.py'):
                python_files.append(os.path.join(root, f))
    
    print(f'发现 {len(python_files)} 个Python文件')
    
    for file_path in python_files:
        file_errors = check_syntax(file_path)
        if file_errors:
            errors.extend(file_errors)
            print(f'❌ {file_path}: {len(file_errors)} 个错误')
        else:
            print(f'✅ {file_path}')
    
    return errors

def main():
    print('=== 后端工程师AI - 全面代码错误检查 ===')
    print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    # 创建错误报告表
    conn = sqlite3.connect('flask-app/app.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS error_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT,
            error_message TEXT,
            file_path TEXT,
            line_number INTEGER,
            timestamp TEXT,
            fixed INTEGER DEFAULT 0,
            fix_description TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
    # 检查所有Python文件
    print('检查Python文件语法...')
    errors = check_all_files()
    
    # 报告错误到数据库
    print(f'\n报告 {len(errors)} 个错误到数据库...')
    for err in errors:
        report_error(
            err['type'],
            err['message'],
            err.get('file'),
            err.get('line')
        )
    
    # 统计
    print(f'\n=== 检查完成 ===')
    print(f'发现错误: {len(errors)} 个')
    
    # 查询数据库确认报告
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM error_reports')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM error_reports WHERE fixed = 0')
    unfixed = cursor.fetchone()[0]
    conn.close()
    
    print(f'数据库中总错误记录: {total}')
    print(f'未修复错误: {unfixed}')

if __name__ == '__main__':
    main()