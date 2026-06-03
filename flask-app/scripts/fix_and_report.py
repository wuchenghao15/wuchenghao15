# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复方案上报系统
将所有修复方案记录到数据库,供AI学习
"""

import os
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List
import sys

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


def log(message: str, symbol: str = '📋'):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} {message}")


def get_db():
    return sqlite3.connect(DATABASE_PATH)


def report_fix(error_type: str, file_path: str, issue: str, fix_description: str, 
               original_code: str, fixed_code: str, success: bool = True):
    """上报修复方案到数据库"""
    fix_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 记录修复方案
        cursor.execute('''
            INSERT INTO error_fixes 
            (id, error_id, fix_code, fix_description, success, applied_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            fix_id,
            f'FIX_{now.replace(":", "").replace("-", "").replace(".", "")}',
            json.dumps({
                'error_type': error_type,
                'file': file_path,
                'original': original_code,
                'fixed': fixed_code
            }, ensure_ascii=False),
            fix_description,
            1 if success else 0,
            now
        ))
        
        conn.commit()
        log(f"已上报修复方案: {error_type} in {file_path}", '✅')
        return True
        
    except Exception as e:
        log(f"上报失败: {e}", '❌')
        return False
    finally:
        conn.close()


def report_error(error_type: str, file_path: str, line: int, issue: str, 
                 code: str, severity: str = 'medium'):
    """上报错误到数据库"""
    error_id = str(uuid.uuid4())
    error_code = f'ERR_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    now = datetime.now().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO error_diagnostics
            (id, error_code, error_type, severity, file_path, line_number, error_message, stack_trace, occurred_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (error_id, error_code, error_type, severity, file_path, line, issue, code, now, 'reported'))
        
        conn.commit()
        log(f"已上报错误: {error_type} - {issue}", '⚠️')
        return error_id
        
    except Exception as e:
        log(f"上报错误失败: {e}", '❌')
        return None
    finally:
        conn.close()


def report_system_fix():
    """上报系统修复记录"""
    log('=' * 60, '📋')
    log('开始上报修复方案到数据库', '📋')
    log('=' * 60, '📋')
    
    fixes = [
        {
            'error_type': 'template',
            'file': 'templates/set_grade.html',
            'issue': 'Jinja2模板使用Python方法而非过滤器',
            'fix': '将 grade.replace("年级", "") 替换为 grade | replace("年级", "")',
            'original': '{{ grade.replace("年级", "") }}',
            'fixed': '{{ grade | replace("年级", "") }}',
            'lines': '277, 292, 306, 320'
        },
        {
            'error_type': 'javascript',
            'file': 'templates/set_grade.html',
            'issue': 'JavaScript依赖全局event对象',
            'fix': '通过遍历按钮匹配年级名称,避免依赖event.target',
            'original': 'event.target.classList.add("selected")',
            'fixed': 'buttons.forEach(btn => { if(...) btn.classList.add("selected") })',
            'lines': '433-440'
        },
        {
            'error_type': 'security',
            'file': 'templates/set_grade.html',
            'issue': '潜在XSS风险 - innerHTML未转义',
            'fix': '添加escapeHtml函数对用户输入进行转义',
            'original': 'bankItem.innerHTML = `...${data}...`',
            'fixed': 'bankItem.innerHTML = escapeHtml(data) + ...',
            'lines': '468'
        },
        {
            'error_type': 'duplicate_route',
            'file': 'app.py',
            'issue': '路由 /api/exams 被多次定义',
            'fix': '使用methods参数区分不同HTTP方法,而非重复路由',
            'original': '@app.route("/api/exams") + @app.route("/api/exams")',
            'fixed': '@app.route("/api/exams", methods=["GET", "POST"])',
            'lines': '925, 1041'
        },
        {
            'error_type': 'code_quality',
            'file': 'app/blueprints/notification_api.py',
            'issue': '数据库连接可能未关闭',
            'fix': '使用with语句确保连接自动关闭',
            'original': 'conn = get_db() ... conn.close()',
            'fixed': 'with get_db() as conn: ...',
            'lines': '24'
        },
        {
            'error_type': 'api_blueprint',
            'file': 'app.py',
            'issue': '蓝图admin_api已注册,诊断误报',
            'fix': 'admin_api和config_api蓝图已在app.py中正确注册',
            'original': '未注册',
            'fixed': 'from app.routes.admin_api import admin_api_bp; app.register_blueprint(admin_api_bp)',
            'lines': '62-63, 70-71'
        }
    ]
    
    success_count = 0
    for fix in fixes:
        if report_fix(
            fix['error_type'],
            fix['file'],
            fix['issue'],
            f"修复方法: {fix['fix']} | 影响行: {fix['lines']}",
            fix['original'],
            fix['fixed']
        ):
            success_count += 1
    
    log(f"=' * 60", '📊')
    log(f"成功上报 {success_count}/{len(fixes)} 个修复方案", '📊')
    log(f"=' * 60", '📊')


def generate_fix_report():
    """生成修复报告"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM error_fixes WHERE success = 1')
    total_fixes = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM error_fixes WHERE success = 1')
    fix_by_type = {'template': 0, 'javascript': 0, 'security': 0, 'duplicate_route': 0, 'code_quality': 0, 'api_blueprint': 0}
    
    cursor.execute('SELECT * FROM error_fixes WHERE success = 1 ORDER BY applied_at DESC LIMIT 10')
    recent_fixes = []
    for row in cursor.fetchall():
        fix_data = json.loads(row[2]) if row[2] else {}
        recent_fixes.append({
            'id': row[0],
            'error_id': row[1],
            'fix_type': fix_data.get('error_type', 'unknown'),
            'file': fix_data.get('file', ''),
            'description': row[3],
            'applied_at': row[4]
        })
    
    conn.close()
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_fixes': total_fixes,
        'fixes_by_type': fix_by_type,
        'recent_fixes': recent_fixes,
        'recommendations': [
            '建议对所有用户输入进行HTML转义',
            'Jinja2模板中避免使用Python方法调用',
            'JavaScript中避免依赖全局event对象',
            '路由定义使用methods参数区分不同操作',
            '数据库连接使用with语句自动管理'
        ],
        'ai_learning_notes': [
            'Jinja2过滤器与Python方法的区别需要AI学习',
            'XSS防护的重要性需要AI理解',
            '代码质量规范需要AI遵循'
        ]
    }
    
    return report


def main():
    log('\n' + '=' * 60, '🔧')
    log('修复方案上报系统', '🔧')
    log('=' * 60, '\n')
    
    # 上报修复方案
    report_system_fix()
    
    # 生成报告
    report = generate_fix_report()
    
    log('\n' + '=' * 60, '📊')
    log('修复报告摘要', '📊')
    log('=' * 60, '📊')
    log(f"总修复数: {report['total_fixes']}", '📊')
    
    log('修复类型分布:', '📈')
    for fix_type, count in report['fixes_by_type'].items():
        log(f"  - {fix_type}: {count}", '📈')
    
    log('AI学习建议:', '🧠')
    for i, note in enumerate(report['ai_learning_notes'], 1):
        log(f"  {i}. {note}", '🧠')
    
    # 保存报告
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'reports',
        f'fix_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    log(f'\n报告已保存: {report_path}', '📁')
    
    print('\n' + '=' * 60)
    log('修复方案上报完成', '✅')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    main()
