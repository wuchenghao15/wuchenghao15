#!/usr/bin/env python3
import os
import ast
import sqlite3

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_files = [row['file_path'] for row in cursor.fetchall()]

fixed_count = 0
still_failed = []

def find_closing_paren(s, start):
    count = 1
    i = start
    in_string = False
    string_char = ''
    escape = False
    while i < len(s) and count > 0:
        i += 1
        if i >= len(s):
            break
        if escape:
            escape = False
            continue
        if s[i] == '\\':
            escape = True
            continue
        if s[i] == string_char:
            in_string = False
        elif s[i] in ('"', "'") and not in_string:
            in_string = True
            string_char = s[i]
        elif not in_string:
            if s[i] == '(':
                count += 1
            elif s[i] == ')':
                count -= 1
    return i

def split_line(line):
    stripped = line.strip()
    if not stripped:
        return [line]
    
    indent = len(line) - len(stripped)
    results = []
    
    while stripped:
        matched = False
        
        if stripped.startswith('"""'):
            end_idx = stripped.find('"""', 3)
            if end_idx != -1:
                doc_end = end_idx + 3
                doc_part = stripped[:doc_end]
                after_doc = stripped[doc_end:].strip()
                results.append(' ' * indent + doc_part)
                if after_doc:
                    stripped = after_doc
                    matched = True
                else:
                    stripped = ''
        
        if not matched and 'logger.' in stripped:
            idx = stripped.find('logger.')
            paren_idx = stripped.find('(', idx)
            if paren_idx != -1:
                close_idx = find_closing_paren(stripped, paren_idx)
                if close_idx < len(stripped) - 1:
                    logger_part = stripped[:close_idx + 1]
                    after_logger = stripped[close_idx + 1:].strip()
                    if after_logger:
                        results.append(' ' * indent + logger_part)
                        stripped = after_logger
                        indent += 4
                        matched = True
        
        if not matched and 'print(' in stripped:
            idx = stripped.find('print(')
            close_idx = find_closing_paren(stripped, idx + 5)
            if close_idx < len(stripped) - 1:
                print_part = stripped[:close_idx + 1]
                after_print = stripped[close_idx + 1:].strip()
                if after_print:
                    results.append(' ' * indent + print_part)
                    stripped = after_print
                    indent += 4
                    matched = True
        
        if not matched and 'cursor.execute(' in stripped:
            idx = stripped.find('cursor.execute(')
            close_idx = find_closing_paren(stripped, idx + 16)
            if close_idx < len(stripped) - 1:
                exec_part = stripped[:close_idx + 1]
                after_exec = stripped[close_idx + 1:].strip()
                if after_exec:
                    results.append(' ' * indent + exec_part)
                    stripped = after_exec
                    matched = True
        
        if not matched and stripped.startswith('def '):
            colon_idx = stripped.find(':')
            if colon_idx != -1:
                def_part = stripped[:colon_idx + 1]
                after_def = stripped[colon_idx + 1:].strip()
                results.append(' ' * indent + def_part)
                if after_def:
                    stripped = after_def
                    indent += 4
                    matched = True
        
        if not matched and stripped.startswith('class '):
            colon_idx = stripped.find(':')
            if colon_idx != -1:
                class_part = stripped[:colon_idx + 1]
                after_class = stripped[colon_idx + 1:].strip()
                results.append(' ' * indent + class_part)
                if after_class:
                    stripped = after_class
                    indent += 4
                    matched = True
        
        if not matched:
            keywords = ['if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except ', 'finally:', 'with ']
            for kw in keywords:
                idx = stripped.find(kw)
                if idx == 0:
                    colon_idx = stripped.find(':')
                    if colon_idx != -1:
                        kw_part = stripped[:colon_idx + 1]
                        after_kw = stripped[colon_idx + 1:].strip()
                        results.append(' ' * indent + kw_part)
                        if after_kw:
                            stripped = after_kw
                            indent += 4
                            matched = True
                        else:
                            stripped = ''
                        break
        
        if not matched:
            bracket_patterns = [
                (']return', ']', 4),
                (']if', ']', 0),
                ('}return', '}', 4),
                ('}if', '}', 0),
                (')return', ')', 4),
                (')if', ')', 0),
                (')else', ')', 0),
                (')elif', ')', 0),
                (']for', ']', 4),
                ('}for', '}', 4),
                (')for', ')', 4),
                ('")for', '")', 4),
                ("')for", "')", 4),
                ('")if', '")', 0),
                ("')if", "')", 0),
            ]
            for pattern, bracket, extra_indent in bracket_patterns:
                idx = stripped.find(pattern)
                if idx != -1:
                    first_part = stripped[:idx + len(bracket)]
                    second_part = stripped[idx + len(bracket):].strip()
                    results.append(' ' * indent + first_part)
                    if second_part:
                        stripped = second_part
                        indent += extra_indent
                        matched = True
                    else:
                        stripped = ''
                    break
        
        if not matched:
            results.append(' ' * indent + stripped)
            stripped = ''
    
    return results

def fix_file(file_path):
    if not os.path.exists(file_path):
        return False, '文件不存在'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            new_lines.extend(split_line(line))
        
        final_content = '\n'.join(new_lines)
        
        if final_content == original_content:
            return False, '内容未改变'
        
        try:
            ast.parse(final_content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            cursor.execute('''
                UPDATE syntax_repair_logs SET 
                    after_content = ?, 
                    fix_status = "success",
                    verified = 1
                WHERE file_path = ? AND fix_status = "failed"
            ''', (final_content, file_path))
            
            cursor.execute('''
                UPDATE syntax_errors SET status = "fixed" 
                WHERE file_path = ? AND status = "error"
            ''', (file_path,))
            
            conn.commit()
            return True, None
        except SyntaxError as e:
            return False, '仍有语法错误: ' + str(e)
    
    except Exception as e:
        return False, '处理失败: ' + str(e)

for file_path in failed_files:
    print('\n处理: ' + os.path.basename(file_path))
    success, reason = fix_file(file_path)
    
    if success:
        fixed_count += 1
        print('✅ 修复成功!')
    else:
        still_failed.append((file_path, reason))
        print('❌ ' + reason)

conn.commit()
conn.close()

print('\n' + '=' * 80)
print('修复结果:')
print('  成功修复: ' + str(fixed_count))
print('  修复失败: ' + str(len(still_failed)))
print('  总处理数: ' + str(len(failed_files)))
