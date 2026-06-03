# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统错误诊断与修复系统
自动检测代码错误、上报到数据库、生成修复方案
"""

import os
import sys
import sqlite3
import json
import uuid
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import ast
import inspect

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
FLASK_APP_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(message: str, symbol: str = '🔍'):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} {message}")


class ErrorDiagnostics:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixes = []
        self.db_path = DATABASE_PATH
        
    def init_error_tables(self):
        """初始化错误记录表"""
        log('初始化错误记录表...', '📋')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS error_diagnostics (
                id TEXT PRIMARY KEY,
                error_code TEXT UNIQUE,
                error_type TEXT,
                severity TEXT DEFAULT 'medium',
                file_path TEXT,
                line_number INTEGER,
                error_message TEXT,
                stack_trace TEXT,
                occurred_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                status TEXT DEFAULT 'pending'
            )''',
            
            '''CREATE TABLE IF NOT EXISTS error_fixes (
                id TEXT PRIMARY KEY,
                error_id TEXT,
                fix_code TEXT,
                fix_description TEXT,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 0,
                FOREIGN KEY (error_id) REFERENCES error_diagnostics(id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS code_analysis (
                id TEXT PRIMARY KEY,
                file_path TEXT,
                analysis_type TEXT,
                findings TEXT,
                severity TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE IF NOT EXISTS system_health (
                id TEXT PRIMARY KEY,
                check_name TEXT,
                status TEXT,
                details TEXT,
                checked_at TEXT DEFAULT CURRENT_TIMESTAMP
            )'''
        ]
        
        for sql in tables:
            try:
                cursor.execute(sql)
            except Exception as e:
                log(f'创建表失败: {e}', '❌')
        
        conn.commit()
        conn.close()
        log('错误记录表初始化完成', '✅')
    
    def check_database_connection(self) -> bool:
        """检查数据库连接"""
        log('检查数据库连接...', '🔗')
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table"')
            tables = cursor.fetchall()
            cursor.execute('PRAGMA integrity_check')
            integrity = cursor.fetchone()
            conn.close()
            
            if tables[0][0] > 0 and integrity[0] == 'ok':
                log(f'数据库连接正常 ({tables[0][0]} 个表)', '✅')
                self.record_health_check('database', 'healthy', f'{tables[0][0]} tables, integrity ok')
                return True
            else:
                log('数据库完整性检查失败', '⚠️')
                self.record_health_check('database', 'warning', 'tables or integrity issue')
                return False
        except Exception as e:
            log(f'数据库连接失败: {e}', '❌')
            self.record_health_check('database', 'error', str(e))
            return False
    
    def check_template_syntax(self, template_path: str) -> List[Dict]:
        """检查模板语法错误"""
        errors = []
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查Jinja2语法问题
            jinja_issues = [
                (r'\{\{.*\.replace\(', '使用Python方法而非Jinja2过滤器'),
                (r'\{\%.*\{\%.*\%\}', '可能的Jinja2嵌套错误'),
                (r'\{\{.*\}\}\}', '未闭合的Jinja2标签'),
                (r'\{\%.*\%\}\}', '未闭合的Jinja2块标签'),
            ]
            
            for pattern, issue_type in jinja_issues:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    errors.append({
                        'file': template_path,
                        'line': line_num,
                        'type': 'template',
                        'issue': issue_type,
                        'code': match.group()
                    })
            
            # 检查JavaScript语法
            js_pattern = r'<script[^>]*>(.*?)</script>'
            js_matches = re.finditer(js_pattern, content, re.DOTALL)
            
            for js_match in js_matches:
                js_code = js_match.group(1)
                # 检查常见的JS问题
                if re.search(r'event\.target', js_code):
                    line_offset = content[:js_match.start()].count('\n')
                    errors.append({
                        'file': template_path,
                        'line': line_offset + 1,
                        'type': 'javascript',
                        'issue': '依赖全局event对象',
                        'code': 'event.target'
                    })
                
                # 检查未转义的用户输入
                if re.search(r'innerHTML\s*=\s*[\'"](?!<)', js_code) and '{{' in js_code:
                    errors.append({
                        'file': template_path,
                        'line': line_offset + 1,
                        'type': 'security',
                        'issue': '潜在的XSS风险',
                        'code': 'innerHTML with user data'
                    })
        
        except Exception as e:
            errors.append({
                'file': template_path,
                'line': 0,
                'type': 'file',
                'issue': f'文件读取失败: {e}',
                'code': ''
            })
        
        return errors
    
    def check_python_syntax(self, file_path: str) -> List[Dict]:
        """检查Python语法错误"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试解析AST
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append({
                    'file': file_path,
                    'line': e.lineno or 0,
                    'type': 'syntax',
                    'issue': str(e),
                    'code': e.text
                })
            
            # 检查常见代码问题
            issues = [
                (r'except\s*:\s*$', '裸except子句应指定异常类型'),
                (r'sqlite3\.connect\([^)]*\)\s*$', '数据库连接可能未关闭'),
                (r'print\s*\([^)]{100,}\)', 'print语句过长'),
            ]
            
            for pattern, issue_type in issues:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    errors.append({
                        'file': file_path,
                        'line': line_num,
                        'type': 'code_quality',
                        'issue': issue_type,
                        'code': match.group()[:50]
                    })
        
        except Exception as e:
            errors.append({
                'file': file_path,
                'line': 0,
                'type': 'file',
                'issue': f'文件读取失败: {e}',
                'code': ''
            })
        
        return errors
    
    def check_api_endpoints(self) -> List[Dict]:
        """检查API端点"""
        errors = []
        
        app_py = os.path.join(FLASK_APP_PATH, 'app.py')
        
        try:
            with open(app_py, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找@app.route装饰器
            route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"]'
            routes = re.findall(route_pattern, content)
            
            # 检查重复路由
            from collections import Counter
            route_counts = Counter(routes)
            
            for route, count in route_counts.items():
                if count > 1:
                    errors.append({
                        'file': app_py,
                        'line': 0,
                        'type': 'duplicate_route',
                        'issue': f'路由 {route} 被定义了 {count} 次',
                        'code': route
                    })
            
            # 检查未注册的蓝图
            blueprint_pattern = r'from\s+.*\s+import\s+(\w+_api|\w+_bp)'
            blueprints = re.findall(blueprint_pattern, content)
            register_pattern = r'app\.register_blueprint\((\w+_api|\w+_bp)\)'
            registered = re.findall(register_pattern, content)
            
            for bp in blueprints:
                if bp not in registered:
                    errors.append({
                        'file': app_py,
                        'line': 0,
                        'type': 'unregistered_blueprint',
                        'issue': f'蓝图 {bp} 未注册',
                        'code': bp
                    })
        
        except Exception as e:
            errors.append({
                'file': app_py,
                'line': 0,
                'type': 'file',
                'issue': f'文件读取失败: {e}',
                'code': ''
            })
        
        return errors
    
    def check_file_structure(self) -> List[Dict]:
        """检查文件结构"""
        errors = []
        
        required_files = [
            'app.py',
            'templates/index.html',
            'app.db'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(FLASK_APP_PATH, file_path)
            if not os.path.exists(full_path):
                errors.append({
                    'file': file_path,
                    'line': 0,
                    'type': 'missing_file',
                    'issue': f'必需文件缺失: {file_path}',
                    'code': ''
                })
        
        # 检查templates目录中的html文件
        templates_dir = os.path.join(FLASK_APP_PATH, 'templates')
        if os.path.exists(templates_dir):
            for file in os.listdir(templates_dir):
                if file.endswith('.html'):
                    template_path = os.path.join(templates_dir, file)
                    template_errors = self.check_template_syntax(template_path)
                    errors.extend(template_errors)
        
        # 检查blueprints目录
        blueprints_dir = os.path.join(FLASK_APP_PATH, 'app', 'blueprints')
        if os.path.exists(blueprints_dir):
            for file in os.listdir(blueprints_dir):
                if file.endswith('.py'):
                    bp_path = os.path.join(blueprints_dir, file)
                    py_errors = self.check_python_syntax(bp_path)
                    errors.extend(py_errors)
        
        return errors
    
    def record_error(self, error_data: Dict) -> str:
        """记录错误到数据库"""
        error_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO error_diagnostics 
                (id, error_code, error_type, severity, file_path, line_number, error_message, stack_trace)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                error_id,
                f'ERR_{datetime.now().strftime("%Y%m%d%H%M%S")}_{len(self.errors)}',
                error_data.get('type', 'unknown'),
                error_data.get('severity', 'medium'),
                error_data.get('file', ''),
                error_data.get('line', 0),
                error_data.get('issue', ''),
                error_data.get('code', '')
            ))
            
            conn.commit()
        except Exception as e:
            log(f'记录错误失败: {e}', '❌')
        finally:
            conn.close()
        
        return error_id
    
    def record_health_check(self, check_name: str, status: str, details: str = ''):
        """记录健康检查结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_health (id, check_name, status, details)
            VALUES (?, ?, ?, ?)
        ''', (str(uuid.uuid4()), check_name, status, details))
        
        conn.commit()
        conn.close()
    
    def record_fix(self, error_id: str, fix_code: str, description: str, success: bool = True):
        """记录修复方案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_fixes (id, error_id, fix_code, fix_description, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), error_id, fix_code, description, 1 if success else 0))
        
        cursor.execute('''
            UPDATE error_diagnostics SET status = 'resolved', resolved_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), error_id))
        
        conn.commit()
        conn.close()
    
    def run_diagnostics(self):
        """运行完整诊断"""
        log('=' * 60, '🔍')
        log('开始系统错误诊断', '🔍')
        log('=' * 60, '🔍')
        
        self.init_error_tables()
        
        # 1. 数据库连接检查
        db_ok = self.check_database_connection()
        
        # 2. API端点检查
        log('检查API端点...', '🔗')
        api_errors = self.check_api_endpoints()
        for error in api_errors:
            self.record_error(error)
            self.errors.append(error)
            log(f"  API错误: {error['issue']}", '⚠️')
        
        # 3. 文件结构检查
        log('检查文件结构和语法...', '📁')
        file_errors = self.check_file_structure()
        for error in file_errors:
            self.record_error(error)
            self.errors.append(error)
            if error['type'] in ['template', 'python']:
                log(f"  {error['type']}错误 [{error['file']}:{error['line']}] {error['issue']}", '⚠️')
            else:
                log(f"  {error['type']}: {error['issue']}", '⚠️')
        
        # 4. 系统健康检查
        log('执行系统健康检查...', '💚')
        self.record_health_check('app_py', 'healthy' if os.path.exists(os.path.join(FLASK_APP_PATH, 'app.py')) else 'error')
        self.record_health_check('templates', 'healthy' if os.path.exists(os.path.join(FLASK_APP_PATH, 'templates')) else 'error')
        
        # 总结
        log('=' * 60, '📊')
        log(f'诊断完成: 发现 {len(self.errors)} 个问题', '📊')
        log('=' * 60, '📊')
        
        # 输出错误摘要
        if self.errors:
            error_types = {}
            for error in self.errors:
                error_type = error['type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            log('错误类型统计:', '📈')
            for error_type, count in error_types.items():
                log(f'  - {error_type}: {count}个', '📈')
        
        return self.errors
    
    def apply_autofixes(self):
        """应用自动修复"""
        log('=' * 60, '🔧')
        log('开始自动修复', '🔧')
        log('=' * 60, '🔧')
        
        fixed_count = 0
        
        for error in self.errors:
            if error['type'] == 'template':
                if 'Python方法' in error['issue']:
                    fix_result = self.fix_jinja2_filter_error(error)
                    if fix_result:
                        fixed_count += 1
                        self.record_fix(
                            self.record_error(error),
                            'replace_python_method',
                            '将Python方法调用替换为Jinja2过滤器'
                        )
            
            elif error['type'] == 'javascript':
                if 'event.target' in error['code']:
                    fix_result = self.fix_event_target_error(error)
                    if fix_result:
                        fixed_count += 1
                        self.record_fix(
                            self.record_error(error),
                            'pass_event_param',
                            '将event作为参数传递而非使用全局对象'
                        )
        
        log(f'自动修复完成: 修复了 {fixed_count} 个问题', '✅')
        return fixed_count
    
    def fix_jinja2_filter_error(self, error: Dict) -> bool:
        """修复Jinja2过滤器错误"""
        try:
            with open(error['file'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换 .replace() 为 | replace
            fixed_content = re.sub(
                r'\{\{\s*([^\}]+)\.replace\(([^\)]+)\)\s*\}\}',
                r'{{ \1 | replace(\2) }}',
                content
            )
            
            if content != fixed_content:
                with open(error['file'], 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                log(f"  已修复: {error['file']}", '✅')
                return True
        except Exception as e:
            log(f"  修复失败: {e}", '❌')
        
        return False
    
    def fix_event_target_error(self, error: Dict) -> bool:
        """修复event.target错误"""
        try:
            with open(error['file'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换 event.target 为通过参数传递的btn
            fixed_content = content.replace('event.target.classList', 'btn.classList')
            
            if content != fixed_content:
                with open(error['file'], 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                log(f"  已修复: {error['file']}", '✅')
                return True
        except Exception as e:
            log(f"  修复失败: {e}", '❌')
        
        return False
    
    def generate_report(self) -> Dict:
        """生成诊断报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM error_diagnostics WHERE status = "pending"')
        pending_errors = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM error_diagnostics WHERE status = "resolved"')
        resolved_errors = cursor.fetchone()[0]
        
        cursor.execute('SELECT error_type, COUNT(*) FROM error_diagnostics GROUP BY error_type')
        error_breakdown = dict(cursor.fetchall())
        
        cursor.execute('SELECT * FROM system_health ORDER BY checked_at DESC LIMIT 10')
        health_history = []
        for row in cursor.fetchall():
            health_history.append({
                'check_name': row[1],
                'status': row[2],
                'details': row[3],
                'checked_at': row[4]
            })
        
        conn.close()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_errors': pending_errors + resolved_errors,
                'pending_errors': pending_errors,
                'resolved_errors': resolved_errors,
                'error_breakdown': error_breakdown
            },
            'health_checks': health_history,
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if len(self.errors) > 0:
            recommendations.append('建议运行完整的代码审查,修复已发现的错误')
        
        if any(e['type'] == 'security' for e in self.errors):
            recommendations.append('发现安全相关问题,建议立即修复XSS风险')
        
        if any(e['type'] == 'duplicate_route' for e in self.errors):
            recommendations.append('存在重复路由定义,建议合并或重命名')
        
        if not recommendations:
            recommendations.append('系统状态良好,建议保持定期诊断习惯')
        
        return recommendations


def main():
    diagnostics = ErrorDiagnostics()
    
    # 运行诊断
    diagnostics.run_diagnostics()
    
    # 应用自动修复
    diagnostics.apply_autofixes()
    
    # 生成报告
    report = diagnostics.generate_report()
    
    log('=' * 60, '📊')
    log('诊断报告', '📊')
    log('=' * 60, '📊')
    log(f"总错误数: {report['summary']['total_errors']}", '📊')
    log(f"待处理: {report['summary']['pending_errors']}", '⚠️')
    log(f"已解决: {report['summary']['resolved_errors']}", '✅')
    
    log('错误分布:', '📈')
    for error_type, count in report['summary']['error_breakdown'].items():
        log(f'  - {error_type}: {count}', '📈')
    
    log('改进建议:', '💡')
    for i, rec in enumerate(report['recommendations'], 1):
        log(f'  {i}. {rec}', '💡')
    
    # 保存报告到文件
    report_path = os.path.join(FLASK_APP_PATH, 'reports', f'diagnostics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    log(f'报告已保存到: {report_path}', '📁')
    
    print('\n' + '=' * 60)
    log('错误诊断与修复完成', '✅')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    main()
