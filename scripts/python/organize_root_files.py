#!/usr/bin/env python3
"""
项目根目录文件整理工具
将临时脚本、数据库文件、日志文件等整理到合适的子目录
"""

import os
import shutil
import time
import json
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def organize_root_files(dry_run=False) -> dict:
    """整理项目根目录文件"""
    result = {
        'organized_count': 0,
        'cleaned_count': 0,
        'removed_count': 0,
        'sync_count': 0,
        'organized_files': [],
        'cleaned_files': [],
        'removed_dirs': [],
        'synced_files': [],
        'errors': [],
    }

    os.makedirs(os.path.join(PROJECT_ROOT, 'scripts/debug'), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, 'data/databases'), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, 'scripts/fix'), exist_ok=True)

    # 整理调试脚本
    debug_scripts = sorted([f for f in os.listdir(PROJECT_ROOT) 
                           if f.startswith('_') and f.endswith('.py')])
    for fname in debug_scripts:
        src = os.path.join(PROJECT_ROOT, fname)
        dst = os.path.join(PROJECT_ROOT, 'scripts/debug', fname)
        
        if os.path.exists(dst):
            fname_no_ext = os.path.splitext(fname)[0]
            dst = os.path.join(PROJECT_ROOT, 'scripts/debug', f'{fname_no_ext}_{int(time.time())}.py')
        
        if not dry_run:
            try:
                shutil.move(src, dst)
                result['organized_count'] += 1
                result['organized_files'].append(f'{fname} -> scripts/debug/')
            except Exception as e:
                result['errors'].append(f'移动失败 {fname}: {e}')
        else:
            result['organized_files'].append(f'{fname} -> scripts/debug/')

    # 整理fix脚本
    fix_scripts = sorted([f for f in os.listdir(PROJECT_ROOT) 
                         if f.startswith('fix_') and f.endswith('.py')])
    for fname in fix_scripts:
        src = os.path.join(PROJECT_ROOT, fname)
        dst = os.path.join(PROJECT_ROOT, 'scripts/fix', fname)
        
        if os.path.exists(dst):
            fname_no_ext = os.path.splitext(fname)[0]
            dst = os.path.join(PROJECT_ROOT, 'scripts/fix', f'{fname_no_ext}_{int(time.time())}.py')
        
        if not dry_run:
            try:
                shutil.move(src, dst)
                result['organized_count'] += 1
                result['organized_files'].append(f'{fname} -> scripts/fix/')
            except Exception as e:
                result['errors'].append(f'移动失败 {fname}: {e}')
        else:
            result['organized_files'].append(f'{fname} -> scripts/fix/')

    # 整理数据库文件（排除符号链接）
    db_files = sorted([f for f in os.listdir(PROJECT_ROOT) 
                      if f.endswith('.db') and not os.path.islink(os.path.join(PROJECT_ROOT, f))])
    for fname in db_files:
        src = os.path.join(PROJECT_ROOT, fname)
        dst = os.path.join(PROJECT_ROOT, 'data/databases', fname)
        
        if os.path.exists(dst):
            fname_no_ext = os.path.splitext(fname)[0]
            dst = os.path.join(PROJECT_ROOT, 'data/databases', f'{fname_no_ext}_{int(time.time())}.db')
        
        if not dry_run:
            try:
                shutil.move(src, dst)
                result['organized_count'] += 1
                result['organized_files'].append(f'{fname} -> data/databases/')
            except Exception as e:
                result['errors'].append(f'移动失败 {fname}: {e}')
        else:
            result['organized_files'].append(f'{fname} -> data/databases/')

    # 整理日志文件
    log_files = sorted([f for f in os.listdir(PROJECT_ROOT) if f.endswith('.log')])
    for fname in log_files:
        src = os.path.join(PROJECT_ROOT, fname)
        dst = os.path.join(PROJECT_ROOT, 'logs', fname)
        
        if os.path.exists(dst):
            fname_no_ext = os.path.splitext(fname)[0]
            dst = os.path.join(PROJECT_ROOT, 'logs', f'{fname_no_ext}_{int(time.time())}.log')
        
        if not dry_run:
            try:
                shutil.move(src, dst)
                result['organized_count'] += 1
                result['organized_files'].append(f'{fname} -> logs/')
            except Exception as e:
                result['errors'].append(f'移动失败 {fname}: {e}')
        else:
            result['organized_files'].append(f'{fname} -> logs/')

    # 清理临时文件（.tmp, .chk）
    temp_files = sorted([f for f in os.listdir(PROJECT_ROOT) 
                        if f.endswith('.tmp') or f.endswith('.chk')])
    for fname in temp_files:
        fpath = os.path.join(PROJECT_ROOT, fname)
        if not dry_run:
            try:
                os.remove(fpath)
                result['cleaned_count'] += 1
                result['cleaned_files'].append(fname)
            except Exception as e:
                result['errors'].append(f'删除失败 {fname}: {e}')
        else:
            result['cleaned_files'].append(fname)

    # 清理临时目录
    temp_dirs = ['.tmp', '.sync_temp_dir']
    for dname in temp_dirs:
        dpath = os.path.join(PROJECT_ROOT, dname)
        if os.path.isdir(dpath):
            if not dry_run:
                try:
                    shutil.rmtree(dpath)
                    result['cleaned_count'] += 1
                    result['cleaned_files'].append(dname)
                except Exception as e:
                    result['errors'].append(f'删除失败 {dname}: {e}')
            else:
                result['cleaned_files'].append(dname)

    # 清理空目录
    empty_dir_candidates = ['Backups', 'ISO_Images', 'archive']
    for dname in empty_dir_candidates:
        dpath = os.path.join(PROJECT_ROOT, dname)
        if os.path.isdir(dpath):
            if not os.listdir(dpath):
                if not dry_run:
                    try:
                        os.rmdir(dpath)
                        result['removed_count'] += 1
                        result['removed_dirs'].append(dname)
                    except Exception as e:
                        result['errors'].append(f'删除失败 {dname}: {e}')
                else:
                    result['removed_dirs'].append(dname)

    return result


def sync_json_to_database(dry_run=False) -> dict:
    """自动上传同步JSON数据到数据库"""
    result = {
        'synced_count': 0,
        'synced_files': [],
        'errors': [],
    }
    
    json_files = sorted([f for f in os.listdir(PROJECT_ROOT) if f.endswith('.json')])
    
    db_path = os.path.join(PROJECT_ROOT, 'data/databases', 'app.db')
    
    if not dry_run:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_path TEXT,
                    record_count INTEGER DEFAULT 0,
                    sync_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            conn.commit()
        except Exception as e:
            result['errors'].append(f'初始化数据库失败: {e}')
            return result
    
    for fname in json_files:
        fpath = os.path.join(PROJECT_ROOT, fname)
        
        if not dry_run:
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                record_count = len(data) if isinstance(data, list) else 1
                
                cursor.execute('''
                    INSERT INTO json_sync_logs (file_name, file_path, record_count, sync_time, status)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                ''', (fname, fpath, record_count, 'success'))
                conn.commit()
                
                result['synced_count'] += 1
                result['synced_files'].append(f'{fname} (记录数: {record_count})')
            except Exception as e:
                result['errors'].append(f'同步失败 {fname}: {e}')
        else:
            result['synced_files'].append(fname)
    
    if not dry_run and 'conn' in locals():
        conn.close()
    
    return result


def get_root_organization_issues() -> list:
    """检查根目录需要整理的问题"""
    issues = []
    debug_count = len([f for f in os.listdir(PROJECT_ROOT) if f.startswith('_') and f.endswith('.py')])
    fix_count = len([f for f in os.listdir(PROJECT_ROOT) if f.startswith('fix_') and f.endswith('.py')])
    db_count = len([f for f in os.listdir(PROJECT_ROOT) if f.endswith('.db') and not os.path.islink(os.path.join(PROJECT_ROOT, f))])
    log_count = len([f for f in os.listdir(PROJECT_ROOT) if f.endswith('.log')])
    temp_file_count = len([f for f in os.listdir(PROJECT_ROOT) if f.endswith('.tmp') or f.endswith('.chk')])
    json_count = len([f for f in os.listdir(PROJECT_ROOT) if f.endswith('.json')])
    
    if debug_count > 0:
        issues.append({
            'issue_type': 'root_debug_scripts',
            'severity': 'low',
            'file_path': PROJECT_ROOT,
            'line_number': 0,
            'error_message': f'根目录有{debug_count}个调试脚本（_开头），建议整理到scripts/debug/',
            'error_code': 'ROOT_DEBUG_SCRIPTS',
            'confidence': 0.9,
        })
    
    if fix_count > 0:
        issues.append({
            'issue_type': 'root_fix_scripts',
            'severity': 'low',
            'file_path': PROJECT_ROOT,
            'line_number': 0,
            'error_message': f'根目录有{fix_count}个修复脚本（fix_开头），建议整理到scripts/fix/',
            'error_code': 'ROOT_FIX_SCRIPTS',
            'confidence': 0.9,
        })
    
    if db_count > 0:
        issues.append({
            'issue_type': 'root_db_files',
            'severity': 'medium',
            'file_path': PROJECT_ROOT,
            'line_number': 0,
            'error_message': f'根目录有{db_count}个数据库文件，建议整理到data/databases/',
            'error_code': 'ROOT_DB_FILES',
            'confidence': 0.8,
        })
    
    if log_count > 0:
        issues.append({
            'issue_type': 'root_log_files',
            'severity': 'low',
            'file_path': PROJECT_ROOT,
            'line_number': 0,
            'error_message': f'根目录有{log_count}个日志文件，建议整理到logs/',
            'error_code': 'ROOT_LOG_FILES',
            'confidence': 0.8,
        })
    
    if temp_file_count > 0:
        issues.append({
            'issue_type': 'root_temp_files',
            'severity': 'medium',
            'file_path': PROJECT_ROOT,
            'line_number': 0,
            'error_message': f'根目录有{temp_file_count}个临时文件（.tmp/.chk），建议删除',
            'error_code': 'ROOT_TEMP_FILES',
            'confidence': 0.9,
        })
    
    if json_count > 0:
        issues.append({
            'issue_type': 'root_json_files',
            'severity': 'low',
            'file_path': PROJECT_ROOT,
            'line_number': 0,
            'error_message': f'根目录有{json_count}个JSON文件，建议同步到数据库',
            'error_code': 'ROOT_JSON_FILES',
            'confidence': 0.7,
        })
    
    temp_dirs = [d for d in ['.tmp', '.sync_temp_dir'] if os.path.isdir(os.path.join(PROJECT_ROOT, d))]
    if temp_dirs:
        issues.append({
            'issue_type': 'root_temp_dirs',
            'severity': 'low',
            'file_path': PROJECT_ROOT,
            'line_number': 0,
            'error_message': f'根目录有临时目录: {", ".join(temp_dirs)}',
            'error_code': 'ROOT_TEMP_DIRS',
            'confidence': 0.7,
        })
    
    empty_dirs = [d for d in ['Backups', 'ISO_Images', 'archive'] if os.path.isdir(os.path.join(PROJECT_ROOT, d)) and not os.listdir(os.path.join(PROJECT_ROOT, d))]
    if empty_dirs:
        issues.append({
            'issue_type': 'root_empty_dirs',
            'severity': 'low',
            'file_path': PROJECT_ROOT,
            'line_number': 0,
            'error_message': f'根目录有空目录: {", ".join(empty_dirs)}',
            'error_code': 'ROOT_EMPTY_DIRS',
            'confidence': 0.8,
        })
    
    return issues


if __name__ == '__main__':
    print('=' * 60)
    print('  项目根目录文件整理工具')
    print('=' * 60)
    
    print('\n--- 检查需要整理的问题 ---')
    issues = get_root_organization_issues()
    if issues:
        for issue in issues:
            print(f"  ⚠️ [{issue['issue_type']}] {issue['error_message']}")
    else:
        print('  ✅ 根目录已经很整洁！')
    
    print('\n--- 开始整理 ---')
    result = organize_root_files(dry_run=False)
    
    print(f'\n整理文件: {result["organized_count"]} 个')
    for f in result['organized_files']:
        print(f'  ✓ {f}')
    
    print(f'\n清理临时文件/目录: {result["cleaned_count"]} 个')
    for d in result['cleaned_files']:
        print(f'  ✓ 删除 {d}')
    
    print(f'\n删除空目录: {result["removed_count"]} 个')
    for d in result['removed_dirs']:
        print(f'  ✓ 删除 {d}')
    
    if result['errors']:
        print(f'\n错误:')
        for e in result['errors']:
            print(f'  ✗ {e}')
    
    print('\n--- 同步JSON数据到数据库 ---')
    sync_result = sync_json_to_database(dry_run=False)
    
    print(f'\n同步JSON文件: {sync_result["synced_count"]} 个')
    for f in sync_result['synced_files']:
        print(f'  ✓ {f}')
    
    if sync_result['errors']:
        print(f'\n同步错误:')
        for e in sync_result['errors']:
            print(f'  ✗ {e}')
    
    print('\n✅ 整理完成！')
