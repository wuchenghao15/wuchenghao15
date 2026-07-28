#!/usr/bin/env python3
import os
import re
import ast
import sqlite3
import tokenize
from io import BytesIO
from collections import Counter

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path, error_message, error_type, before_content FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_records = cursor.fetchall()

print(f'待重试修复文件: {len(failed_records)}')
print('=' * 80)

success_count = 0
fail_count = 0
fixed_files = []
still_failed = []

def fix_eol_string_truncation(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        single_open = False
        double_open = False
        
        if stripped.count("'") % 2 != 0:
            single_open = True
        if stripped.count('"') % 2 != 0:
            double_open = True
        
        if single_open or double_open:
            quote_char = "'" if single_open else '"'
            j = i + 1
            merged = [line]
            total_count = line.count(quote_char)
            
            while j < len(lines):
                next_line = lines[j]
                escaped_count = next_line.count("\\'") if quote_char == "'" else next_line.count('\\"')
                count = next_line.count(quote_char) - escaped_count
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

def fix_multiline_string_literals(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped.startswith("'''") or stripped.startswith('"""'):
            if stripped.count("'''") >= 2 or stripped.count('"""') >= 2:
                fixed_lines.append(line)
                i += 1
                continue
            
            quote_type = "'''" if stripped.startswith("'''") else '"""'
            j = i + 1
            merged = [line]
            
            while j < len(lines):
                next_line = lines[j]
                merged.append(next_line)
                if quote_type in next_line:
                    break
                j += 1
            
            joined = '\n'.join(merged)
            fixed_lines.append(joined)
            i = j + 1
            continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_broken_string_assignment(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        match = re.match(r'(\s*)([\w\[\]]+)\s*=\s*[\'"]', stripped)
        if match:
            indent = match.group(1)
            var_name = match.group(2)
            quote_char = stripped[match.end() - 1]
            
            if stripped.count(quote_char) % 2 != 0:
                j = i + 1
                merged = [line]
                total_count = line.count(quote_char)
                
                while j < len(lines):
                    next_line = lines[j]
                    escaped_count = next_line.count("\\'") if quote_char == "'" else next_line.count('\\"')
                    count = next_line.count(quote_char) - escaped_count
                    total_count += count
                    merged.append(next_line)
                    
                    if total_count % 2 == 0:
                        break
                    j += 1
                
                joined = ''.join([l.rstrip() for l in merged])
                fixed_lines.append(joined)
                i = j + 1
                continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_tokenize_based(content: str) -> str:
    try:
        bytes_content = content.encode('utf-8')
        tokens = list(tokenize.tokenize(BytesIO(bytes_content).readline))
        
        new_tokens = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            
            if tok.type == tokenize.STRING:
                string_value = tok.string
                if len(string_value) >= 2:
                    first_char = string_value[0]
                    last_char = string_value[-1]
                    
                    if (first_char == "'" or first_char == '"') and first_char != last_char:
                        j = i + 1
                        while j < len(tokens):
                            next_tok = tokens[j]
                            if next_tok.type == tokenize.STRING:
                                string_value += next_tok.string
                                i = j
                                break
                            elif next_tok.type == tokenize.NEWLINE or next_tok.type == tokenize.NL:
                                j += 1
                            else:
                                break
            
            new_tokens.append(tok)
            i += 1
        
        if new_tokens:
            return tokenize.untokenize(new_tokens).decode('utf-8')
        return content
    except Exception:
        return content

def fix_generic_errors(content: str) -> str:
    content = fix_eol_string_truncation(content)
    content = fix_multiline_string_literals(content)
    content = fix_broken_string_assignment(content)
    content = fix_tokenize_based(content)
    return content

def test_syntax(content: str) -> bool:
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False

for record in failed_records:
    file_path = record['file_path']
    error_msg = record['error_message']
    error_type = record['error_type']
    before_content = record['before_content']
    
    if not os.path.exists(file_path):
        print(f'❌ 文件不存在: {file_path}')
        fail_count += 1
        still_failed.append((file_path, '文件不存在'))
        continue
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    if before_content and content == before_content:
        pass
    else:
        content = before_content or content
    
    print(f'\n处理: {file_path}')
    print(f'原错误: {error_msg[:80]}')
    
    fixed_content = fix_generic_errors(content)
    
    if test_syntax(fixed_content):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            cursor.execute('''
                UPDATE syntax_repair_logs SET 
                    after_content = ?, 
                    fix_status = "success",
                    verified = 1
                WHERE file_path = ? AND fix_status = "failed"
            ''', (fixed_content, file_path))
            
            conn.commit()
            
            cursor.execute('''
                UPDATE syntax_errors SET status = "fixed" 
                WHERE file_path = ? AND status = "error"
            ''', (file_path,))
            
            conn.commit()
            
            success_count += 1
            fixed_files.append(file_path)
            print('✅ 修复成功!')
        except Exception as e:
            print(f'❌ 写入失败: {e}')
            fail_count += 1
            still_failed.append((file_path, str(e)))
    else:
        print('❌ 修复后仍有语法错误')
        fail_count += 1
        still_failed.append((file_path, '修复后仍有语法错误'))

print('\n' + '=' * 80)
print(f'修复结果:')
print(f'  成功修复: {success_count}')
print(f'  修复失败: {fail_count}')
print(f'  总处理数: {len(failed_records)}')
print(f'  重试成功率: {success_count / len(failed_records) * 100:.1f}%')

if fixed_files:
    print(f'\n成功修复的文件:')
    for fp in fixed_files:
        print(f'  ✓ {fp}')

if still_failed:
    print(f'\n仍未修复的文件:')
    for fp, reason in still_failed[:20]:
        print(f'  ✗ {fp} - {reason}')

conn.close()
