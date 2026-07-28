#!/usr/bin/env python3
"""诊断所有剩余错误文件的错误模式"""
import os
import ast
import sqlite3
from collections import defaultdict

PROJECT_ROOT = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'

def scan_failed_files():
    """扫描所有Python文件，找到有语法错误的"""
    failed = []
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if '.git' in root or '__pycache__' in root or 'venv' in root:
            continue
        # 跳过备份目录
        if 'flask-app-old' in root or 'backup' in root.lower() or 'old' in root.lower():
            continue
        
        for f in files:
            if not f.endswith('.py'):
                continue
            filepath = os.path.join(root, f)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                ast.parse(content)
            except SyntaxError as e:
                rel_path = os.path.relpath(filepath, PROJECT_ROOT)
                failed.append({
                    'path': filepath,
                    'rel_path': rel_path,
                    'line': e.lineno,
                    'msg': e.msg,
                    'offset': e.offset,
                })
            except Exception as e:
                rel_path = os.path.relpath(filepath, PROJECT_ROOT)
                failed.append({
                    'path': filepath,
                    'rel_path': rel_path,
                    'line': 0,
                    'msg': str(e),
                    'offset': 0,
                })
    
    return failed

def analyze_patterns(failed):
    """分析错误模式"""
    patterns = defaultdict(list)
    
    for f in failed:
        msg = f['msg']
        # 归类错误消息
        if 'EOL' in msg:
            category = 'EOL字符串截断'
        elif 'EOF' in msg:
            category = 'EOF字符串截断'
        elif 'unexpected indent' in msg:
            category = '意外缩进'
        elif 'expected an indented block' in msg:
            category = '缺少缩进块'
        elif 'invalid syntax' in msg:
            category = '无效语法'
        elif 'unmatched' in msg:
            category = '不匹配的括号'
        elif 'cannot assign' in msg:
            category = '赋值错误'
        elif 'expected' in msg:
            category = '期望的符号缺失'
        else:
            category = msg
        
        patterns[category].append(f)
    
    return patterns

def show_context(filepath, line_num, context=5):
    """显示错误行的上下文"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        
        result = []
        for i in range(start, end):
            marker = '→' if i == line_num - 1 else ' '
            result.append(f"{marker} {i+1:4d}: {lines[i].rstrip()}")
        
        return '\n'.join(result)
    except:
        return '无法读取文件'

def main():
    print("=" * 70)
    print("MTSCOS 剩余错误文件诊断")
    print("=" * 70)
    
    failed = scan_failed_files()
    print(f"\n共找到 {len(failed)} 个有语法错误的Python文件\n")
    
    patterns = analyze_patterns(failed)
    
    print("错误模式统计:")
    print("-" * 70)
    for category, files in sorted(patterns.items(), key=lambda x: -len(x[1])):
        print(f"  {category:25s}: {len(files):3d} 个文件")
    
    print("\n" + "=" * 70)
    print("详细错误列表:")
    print("=" * 70)
    
    for category, files in sorted(patterns.items(), key=lambda x: -len(x[1])):
        print(f"\n📌 {category} ({len(files)} 个):")
        for f in files[:10]:  # 每个类别最多显示10个
            print(f"  📄 {f['rel_path']}")
            print(f"     行 {f['line']}: {f['msg']}")
            ctx = show_context(f['path'], f['line'], 2)
            for line in ctx.split('\n'):
                print(f"     {line}")
            print()
        if len(files) > 10:
            print(f"  ... 还有 {len(files) - 10} 个文件")

if __name__ == '__main__':
    main()
