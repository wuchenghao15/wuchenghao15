#!/usr/bin/env python3
import ast
import os

def scan_syntax_errors():
    errors = []
    count = 0
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                count += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    ast.parse(content)
                except SyntaxError as e:
                    errors.append({
                        'file': file_path,
                        'line': e.lineno,
                        'msg': str(e)
                    })
                except Exception as e:
                    errors.append({
                        'file': file_path,
                        'line': 0,
                        'msg': f'读取错误: {str(e)}'
                    })
    
    print(f'共扫描 {count} 个Python文件')
    print(f'发现 {len(errors)} 个语法错误文件')
    print('=' * 80)
    
    for i, err in enumerate(errors[:50], 1):
        print(f'{i:3d}. {err["file"]}')
        print(f'     行: {err["line"]}, 错误: {err["msg"]}')
        print()
    
    return errors

if __name__ == '__main__':
    scan_syntax_errors()