#!/usr/bin/env python3
import os
import re
import ast
import sqlite3

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_files = [row['file_path'] for row in cursor.fetchall()]

print(f'待处理失败文件: {len(failed_files)}')

fixed_count = 0
still_failed = []

def fix_string_truncation(content):
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            i += 1
            continue
        
        single_count = line.count("'") - line.count("\\'")
        double_count = line.count('"') - line.count('\\"')
        
        if single_count % 2 != 0 or double_count % 2 != 0:
            quote_char = "'" if single_count % 2 != 0 else '"'
            j = i + 1
            merged = [line]
            total_count = single_count if quote_char == "'" else double_count
            
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                if not next_stripped or next_stripped.startswith('#'):
                    break
                
                escaped = next_line.count("\\'") if quote_char == "'" else next_line.count('\\"')
                count = next_line.count(quote_char) - escaped
                total_count += count
                merged.append(next_line)
                
                if total_count % 2 == 0:
                    break
                j += 1
            
            indent = len(line) - len(stripped)
            joined = ''.join([l.rstrip() for l in merged])
            fixed_lines.append(' ' * indent + joined)
            i = j + 1
            continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_duplicate_statements(content):
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            next_stripped = next_line.strip()
            
            if stripped == next_stripped and stripped.startswith(('cursor.execute', 'conn.execute', 'print', 'return', 'if', 'else')):
                fixed_lines.append(line)
                i += 2
                continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_missing_colons(content):
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        if re.match(r'^\s*(if|elif|else|for|while|def|class|try|except|finally|with)\s+\S', stripped):
            if not stripped.endswith(':'):
                fixed_lines.append(line + ':')
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_indentation(content):
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if line.strip() == '':
            fixed_lines.append('')
            continue
        
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces % 4 != 0 and leading_spaces > 0:
            new_indent = (leading_spaces // 4) * 4
            fixed_lines.append(' ' * new_indent + line.lstrip())
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        content = fix_string_truncation(content)
        content = fix_duplicate_statements(content)
        content = fix_missing_colons(content)
        content = fix_indentation(content)
        
        if content == original_content:
            return False, '内容未变化'
        
        try:
            ast.parse(content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            cursor.execute('''
                UPDATE syntax_repair_logs SET 
                    after_content = ?, 
                    fix_status = "success",
                    verified = 1
                WHERE file_path = ? AND fix_status = "failed"
            ''', (content, file_path))
            
            cursor.execute('''
                UPDATE syntax_errors SET status = "fixed" 
                WHERE file_path = ? AND status = "error"
            ''', (file_path,))
            
            conn.commit()
            
            return True, None
        except SyntaxError as e:
            return False, f'修复后仍有语法错误: {e}'
        except Exception as e:
            return False, f'写入失败: {e}'
    
    except Exception as e:
        return False, f'读取失败: {e}'

for file_path in failed_files:
    if not os.path.exists(file_path):
        print(f'❌ 文件不存在: {file_path}')
        still_failed.append((file_path, '文件不存在'))
        continue
    
    print(f'\n处理: {file_path}')
    success, reason = fix_file(file_path)
    
    if success:
        fixed_count += 1
        print('✅ 修复成功!')
    else:
        still_failed.append((file_path, reason))
        print(f'❌ {reason}')

conn.commit()
conn.close()

print(f'\n{"="*80}')
print(f'修复结果:')
print(f'  成功修复: {fixed_count}')
print(f'  修复失败: {len(still_failed)}')
print(f'  总处理数: {len(failed_files)}')

if still_failed:
    print(f'\n仍未修复的文件:')
    for fp, reason in still_failed[:10]:
        print(f'  ✗ {fp} - {reason}')
