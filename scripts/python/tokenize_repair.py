#!/usr/bin/env python3
import os
import ast
import sqlite3
import io
import tokenize

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_files = [row['file_path'] for row in cursor.fetchall()]

fixed_count = 0
still_failed = []

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
            if not line.strip():
                new_lines.append(line)
                continue
            
            stripped = line.strip()
            indent = line[:len(line) - len(stripped)]
            
            if stripped.startswith('"""'):
                end_doc = stripped.find('"""', 3)
                if end_doc != -1 and end_doc + 3 < len(stripped):
                    doc_part = stripped[:end_doc + 3]
                    code_part = stripped[end_doc + 3:]
                    if code_part.strip():
                        new_lines.append(indent + doc_part)
                        new_lines.append(indent + code_part)
                        continue
            
            if '"""' in stripped:
                parts = stripped.split('"""')
                if len(parts) >= 3:
                    doc_str = '"""'.join(parts[:3])
                    remaining = '"""'.join(parts[3:])
                    if remaining.strip():
                        new_lines.append(indent + doc_str)
                        new_lines.append(indent + remaining)
                        continue
            
            if 'logger.' in stripped and 'return' in stripped:
                idx = stripped.find('return')
                if idx > 0:
                    new_lines.append(indent + stripped[:idx].strip())
                    new_lines.append(indent + '    ' + stripped[idx:].strip())
                    continue
            
            if 'print(' in stripped and 'return' in stripped:
                idx = stripped.find('return')
                if idx > 0:
                    new_lines.append(indent + stripped[:idx].strip())
                    new_lines.append(indent + '    ' + stripped[idx:].strip())
                    continue
            
            if 'cursor.execute(' in stripped and 'except' in stripped:
                idx = stripped.find('except')
                if idx > 0:
                    new_lines.append(indent + stripped[:idx].strip())
                    new_lines.append(indent + stripped[idx:].strip())
                    continue
            
            if 'self.' in stripped and stripped.count('self.') >= 2:
                first_end = stripped.find(' ', stripped.find('self.'))
                if first_end > 0:
                    new_lines.append(indent + stripped[:first_end].strip())
                    new_lines.append(indent + '    ' + stripped[first_end:].strip())
                    continue
            
            if ' = "' in stripped and stripped.count(' = "') >= 2:
                parts = stripped.split(' = "')
                if len(parts) >= 3:
                    end1 = parts[1].find('"')
                    if end1 != -1:
                        new_lines.append(indent + parts[0] + ' = "' + parts[1][:end1 + 1])
                        new_lines.append(indent + ' = "'.join(parts[2:]))
                        continue
            
            if '= "' in stripped and stripped.count('= "') >= 2:
                parts = stripped.split('= "')
                if len(parts) >= 3:
                    end1 = parts[1].find('"')
                    if end1 != -1:
                        new_lines.append(indent + parts[0] + '= "' + parts[1][:end1 + 1])
                        new_lines.append(indent + '= "'.join(parts[2:]))
                        continue
            
            if ':' in stripped and len(stripped) > 50:
                idx = stripped.find(':')
                if idx > 0 and idx + 1 < len(stripped):
                    next_char = stripped[idx + 1]
                    if next_char.isalpha() or next_char.isspace():
                        new_lines.append(indent + stripped[:idx + 1])
                        new_lines.append(indent + '    ' + stripped[idx + 1:].strip())
                        continue
            
            if '[' in stripped and 'for ' in stripped:
                bracket_end = stripped.find(']')
                if bracket_end != -1:
                    for_pos = stripped.find('for ', bracket_end)
                    if for_pos > 0:
                        new_lines.append(indent + stripped[:bracket_end + 1])
                        new_lines.append(indent + '    ' + stripped[for_pos:].strip())
                        continue
            
            if '{' in stripped and 'for ' in stripped:
                brace_end = stripped.find('}')
                if brace_end != -1:
                    for_pos = stripped.find('for ', brace_end)
                    if for_pos > 0:
                        new_lines.append(indent + stripped[:brace_end + 1])
                        new_lines.append(indent + '    ' + stripped[for_pos:].strip())
                        continue
            
            if 'f"' in stripped and 'with ' in stripped:
                f_end = stripped.find('"', stripped.find('f"') + 2)
                if f_end != -1:
                    new_lines.append(indent + stripped[:f_end + 1])
                    new_lines.append(indent + stripped[f_end + 1:].strip())
                    continue
            
            if 'f"' in stripped and 'cursor.execute(' in stripped:
                f_end = stripped.find('"', stripped.find('f"') + 2)
                if f_end != -1:
                    new_lines.append(indent + stripped[:f_end + 1])
                    new_lines.append(indent + stripped[f_end + 1:].strip())
                    continue
            
            if '])for' in stripped:
                new_lines.append(indent + stripped.replace('])for', '])\n        for'))
                continue
            
            if '])if' in stripped:
                new_lines.append(indent + stripped.replace('])if', '])\n        if'))
                continue
            
            if '})for' in stripped:
                new_lines.append(indent + stripped.replace('})for', '})\n        for'))
                continue
            
            if '})if' in stripped:
                new_lines.append(indent + stripped.replace('})if', '})\n        if'))
                continue
            
            if '")for' in stripped:
                new_lines.append(indent + stripped.replace('")for', '")\n        for'))
                continue
            
            if '")if' in stripped:
                new_lines.append(indent + stripped.replace('")if', '")\n        if'))
                continue
            
            if "')for" in stripped:
                new_lines.append(indent + stripped.replace("')for", "')\n        for"))
                continue
            
            if "')if" in stripped:
                new_lines.append(indent + stripped.replace("')if", "')\n        if"))
                continue
            
            new_lines.append(line)
        
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
