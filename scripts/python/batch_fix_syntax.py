#!/usr/bin/env python3
"""
批量修复Python文件语法错误
使用AST解析检测错误，自动修复常见问题
"""

import os
import sys
import ast
import re

def find_python_files(directory):
    """查找目录下所有Python文件"""
    files = []
    for root, dirs, files_in_dir in os.walk(directory):
        for filename in files_in_dir:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))
    return files

def has_syntax_error(filepath):
    """检查文件是否有语法错误"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return e

def fix_file(filepath):
    """修复文件中的语法错误"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            
            str_match = re.search(r'("[^"]*)$', line)
            if str_match and next_line.strip() and not next_line.strip().startswith('"') and not next_line.strip().startswith(','):
                combined = line.rstrip() + next_line.strip()
                fixed_lines.append(combined)
                i += 2
                continue
            
            semicolon_match = re.search(r'(\)\s*:\s*)$', line)
            if semicolon_match and next_line.strip() and not next_line.strip().startswith(' ') and not next_line.strip().startswith('\t'):
                fixed_lines.append(line.rstrip())
                i += 1
                continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_syntax_errors(filepath, error):
    """修复特定语法错误"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    if error.lineno and error.lineno <= len(lines):
        line = lines[error.lineno - 1]
        col_offset = error.offset if error.offset else 0
        
        if 'EOL while scanning string literal' in str(error):
            if error.lineno < len(lines):
                next_line = lines[error.lineno].strip()
                if next_line and not next_line.startswith('"'):
                    lines[error.lineno - 1] = line.rstrip() + next_line
                    del lines[error.lineno]
        
        elif 'invalid syntax' in str(error):
            if col_offset < len(line):
                char_at_pos = line[col_offset]
                if char_at_pos in ')}]':
                    lines[error.lineno - 1] = line[:col_offset] + '\n' + '    ' + line[col_offset:]
    
    return '\n'.join(lines)

def main():
    directory = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/ai_engines'
    python_files = find_python_files(directory)
    
    print(f'发现 {len(python_files)} 个Python文件')
    print('=' * 70)
    
    error_files = []
    for filepath in python_files:
        error = has_syntax_error(filepath)
        if error:
            error_files.append((filepath, error))
            print(f'✗ {filepath}: {error.msg} (行 {error.lineno})')
    
    print('=' * 70)
    print(f'\n共有 {len(error_files)} 个文件存在语法错误')
    
    if error_files:
        print('\n开始修复...')
        for filepath, error in error_files:
            try:
                fixed_content = fix_syntax_errors(filepath, error)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                new_error = has_syntax_error(filepath)
                if new_error:
                    print(f'  ✗ {os.path.basename(filepath)}: 修复失败 - {new_error.msg}')
                else:
                    print(f'  ✓ {os.path.basename(filepath)}: 修复成功')
            except Exception as e:
                print(f'  ✗ {os.path.basename(filepath)}: 修复异常 - {e}')
    
    print('=' * 70)
    print('\n验证修复结果...')
    
    remaining_errors = []
    for filepath in python_files:
        error = has_syntax_error(filepath)
        if error:
            remaining_errors.append((filepath, error))
    
    if remaining_errors:
        print(f'\n仍有 {len(remaining_errors)} 个文件存在语法错误:')
        for filepath, error in remaining_errors:
            print(f'  ✗ {filepath}: {error.msg} (行 {error.lineno})')
    else:
        print('✓ 所有文件语法检查通过！')

if __name__ == '__main__':
    main()
