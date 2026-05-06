#!/usr/bin/env python3
import sqlite3
import ast
import os
import re
from datetime import datetime

def get_unfixed_errors():
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, error_type, error_message, file_path, line_number FROM error_reports WHERE fixed = 0')
    errors = cursor.fetchall()
    conn.close()
    return errors

def mark_error_fixed(error_id, fix_desc):
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE error_reports SET fixed = 1, fix_description = ? WHERE id = ?', (fix_desc, error_id))
    conn.commit()
    conn.close()

def fix_common_syntax_issues(content, file_path):
    fixed_count = 0
    original_content = content

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if re.match(r'^\s*(for|while|if|elif|else|try|except|finally|with|def|class)\s*.*:\s*$', line):
            if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].strip().startswith('#') and not lines[i + 1].strip().startswith('"""') and not lines[i + 1].strip().startswith("'''"):
                if not any(lines[i + 1].startswith(' ') or lines[i + 1].startswith('\t') for _ in [1]):
                    new_lines.append(line)
                    i += 1
                    indent = '    '
                    new_lines.append(indent + 'pass')
                    fixed_count += 1
                    continue
        new_lines.append(line)
        i += 1

    return '\n'.join(new_lines), fixed_count

def attempt_fix_file(file_path):
    if not os.path.exists(file_path):
        return 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed_content, count = fix_common_syntax_issues(content, file_path)

        if count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return count

        ast.parse(content)
        return 0
    except SyntaxError as e:
        try:
            lines = content.split('\n')
            if e.lineno and e.lineno <= len(lines):
                line = lines[e.lineno - 1]

                if 'unindent does not match' in str(e):
                    indent_match = re.search(r'(\s*)\S', line)
                    if indent_match:
                        spaces = indent_match.group(1)
                        expected = len(spaces) + 4
                        fixed_line = ' ' * expected + line.lstrip()
                        lines[e.lineno - 1] = fixed_line
                        fixed_content = '\n'.join(lines)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        return 1

                if 'expected an indented block' in str(e):
                    indent_match = re.search(r'(\s*)', line)
                    spaces = indent_match.group(1) if indent_match else '    '
                    lines.insert(e.lineno, spaces + 'pass')
                    fixed_content = '\n'.join(lines)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    return 1

        except:
            pass
        return 0
    except Exception as e:
        return 0

def main():
    print('=== 自动修复Python语法错误 ===')
    print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    errors = get_unfixed_errors()
    print(f'从数据库读取到 {len(errors)} 个未修复错误')

    unique_files = {}
    for err in errors:
        file_path = err[3]
        if file_path and os.path.exists(file_path):
            if file_path not in unique_files:
                unique_files[file_path] = []
            unique_files[file_path].append(err[0])

    fixed_files = 0
    fixed_errors = 0

    print(f'\n开始修复 {len(unique_files)} 个文件...')

    for file_path, error_ids in unique_files.items():
        if file_path.endswith('.py'):
            print(f'修复: {file_path}...')
            count = attempt_fix_file(file_path)
            if count > 0:
                fixed_files += 1
                fixed_errors += count
                for err_id in error_ids:
                    mark_error_fixed(err_id, f'自动修复了 {count} 处语法问题')

    print(f'\n=== 修复完成 ===')
    print(f'修复文件数: {fixed_files}')
    print(f'修复错误数: {fixed_errors}')

    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM error_reports WHERE fixed = 0')
    remaining = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM error_reports WHERE fixed = 1')
    fixed = cursor.fetchone()[0]
    conn.close()

    print(f'剩余未修复: {remaining}')
    print(f'已修复: {fixed}')

if __name__ == '__main__':
    main()