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
        
        try:
            tokens = list(tokenize.tokenize(io.BytesIO(content.encode()).readline))
        except tokenize.TokenError:
            return False, 'tokenize失败'
        
        new_tokens = []
        skip_tokens = set()
        
        for i, token in enumerate(tokens):
            if i in skip_tokens:
                continue
            
            tok_type, tok_str, start, end, line = token
            
            if tok_type == tokenize.NAME:
                prev_token = tokens[i-1] if i > 0 else None
                next_token = tokens[i+1] if i < len(tokens)-1 else None
                
                if prev_token and prev_token.type == tokenize.STRING and prev_token.string.endswith('"""'):
                    if tok_str in ('def', 'class', 'return', 'if', 'for', 'while', 'with', 'try', 'except', 'finally', 'elif', 'else', 'import', 'from', 'self', 'logger'):
                        new_tokens.append(tokenize.TokenInfo(tokenize.NEWLINE, '\n', start, end, line))
                        new_tokens.append(tokenize.TokenInfo(tokenize.NAME, tok_str, start, end, line))
                        continue
                
                if prev_token and prev_token.type == tokenize.STRING:
                    if tok_str == 'return':
                        new_tokens.append(tokenize.TokenInfo(tokenize.NEWLINE, '\n', start, end, line))
                        new_tokens.append(tokenize.TokenInfo(tokenize.NAME, tok_str, start, end, line))
                        continue
                
                if prev_token and prev_token.type == tokenize.OP and prev_token.string == ')':
                    if tok_str in ('if', 'for', 'while', 'return', 'elif', 'else'):
                        new_tokens.append(tokenize.TokenInfo(tokenize.NEWLINE, '\n', start, end, line))
                        new_tokens.append(tokenize.TokenInfo(tokenize.NAME, tok_str, start, end, line))
                        continue
                
                if prev_token and prev_token.type == tokenize.OP and prev_token.string == ']':
                    if tok_str in ('if', 'for', 'while'):
                        new_tokens.append(tokenize.TokenInfo(tokenize.NEWLINE, '\n', start, end, line))
                        new_tokens.append(tokenize.TokenInfo(tokenize.NAME, tok_str, start, end, line))
                        continue
                
                if prev_token and prev_token.type == tokenize.OP and prev_token.string == '}':
                    if tok_str in ('if', 'for', 'while', 'return'):
                        new_tokens.append(tokenize.TokenInfo(tokenize.NEWLINE, '\n', start, end, line))
                        new_tokens.append(tokenize.TokenInfo(tokenize.NAME, tok_str, start, end, line))
                        continue
            
            if tok_type == tokenize.OP and token.string == 'return':
                prev_token = tokens[i-1] if i > 0 else None
                if prev_token and prev_token.type == tokenize.NAME and prev_token.string in ('logger', 'print'):
                    new_tokens.append(tokenize.TokenInfo(tokenize.NEWLINE, '\n', start, end, line))
                    new_tokens.append(tokenize.TokenInfo(tokenize.OP, 'return', start, end, line))
                    continue
            
            new_tokens.append(token)
        
        try:
            final_content = tokenize.untokenize(new_tokens).decode('utf-8')
        except Exception as e:
            return False, 'untokenize失败: ' + str(e)
        
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
