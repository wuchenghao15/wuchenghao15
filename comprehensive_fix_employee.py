#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面系统修复AI员工 v2.0
扫描并修复所有前端页面的错误，上报修复方案到数据库
"""

import sqlite3
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

class ComprehensiveFixAIEmployee:
    """全面系统修复AI员工"""
    
    def __init__(self, db_path='system_fixes.db'):
        self.db_path = db_path
        self.project_root = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
        self.pages_dir = os.path.join(self.project_root, 'frontend/pages')
        self.employee_name = "全面系统修复工程师"
        self.employee_id = "comprehensive_fix_001"
        self.department = "技术支持部"
        self.fix_count = 0
        self.error_count = 0
        
        self.init_database()
        
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comprehensive_fix_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                employee_id TEXT,
                department TEXT,
                page_name TEXT,
                error_type TEXT,
                error_description TEXT,
                fix_method TEXT,
                fix_code TEXT,
                status TEXT,
                severity TEXT,
                files_affected TEXT,
                details TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fix_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_pages_scanned INTEGER,
                total_errors_found INTEGER,
                total_errors_fixed INTEGER,
                total_warnings INTEGER,
                execution_time TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def log_fix(self, page_name: str, error_type: str, error_desc: str,
                fix_method: str, fix_code: str, status: str,
                severity: str = "medium", files: List[str] = None):
        """记录修复操作"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO comprehensive_fix_logs 
            (timestamp, employee_name, employee_id, department, page_name,
             error_type, error_description, fix_method, fix_code, status,
             severity, files_affected, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            self.employee_name,
            self.employee_id,
            self.department,
            page_name,
            error_type,
            error_desc,
            fix_method,
            fix_code,
            status,
            severity,
            json.dumps(files or []),
            ""
        ))
        
        conn.commit()
        conn.close()
        
        if status == "fixed":
            self.fix_count += 1
            print(f"  ✅ {page_name} - {error_type}: {error_desc[:50]}...")
        else:
            self.error_count += 1
            print(f"  ⚠️  {page_name} - {error_type}: {error_desc[:50]}...")
        
    def scan_all_pages(self) -> List[str]:
        """扫描所有页面文件"""
        pages = []
        if os.path.exists(self.pages_dir):
            for file in os.listdir(self.pages_dir):
                if file.endswith('.html'):
                    pages.append(os.path.join(self.pages_dir, file))
        return pages
        
    def check_cdn_references(self, content: str, page_name: str) -> List[Dict]:
        """检查CDN引用问题"""
        issues = []
        
        # 检查不稳定的CDN
        unstable_cdns = [
            (r'cdnjs\.cloudflare\.com.*font-awesome', 'unstable_font_awesome_cdn',
             '使用不稳定的Font Awesome CDN', 'critical',
             '替换为jsDelivr CDN',
             'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css')
        ]
        
        for pattern, error_type, desc, severity, method, replacement in unstable_cdns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append({
                    'type': error_type,
                    'desc': desc,
                    'severity': severity,
                    'method': method,
                    'pattern': pattern,
                    'replacement': replacement
                })
                
        return issues
        
    def check_css_issues(self, content: str, page_name: str) -> List[Dict]:
        """检查CSS问题"""
        issues = []
        
        # 检查CSS变量是否可能无法加载
        css_vars = re.findall(r'var\(--([a-zA-Z0-9-]+)\)', content)
        if css_vars:
            # 检查是否定义了这些变量
            css_definitions = re.findall(r'--([a-zA-Z0-9-]+)\s*:', content)
            undefined_vars = set(css_vars) - set(css_definitions)
            
            if undefined_vars:
                for var in list(undefined_vars)[:3]:  # 只报告前3个
                    issues.append({
                        'type': 'undefined_css_variable',
                        'desc': f'CSS变量 --{var} 未定义',
                        'severity': 'medium',
                        'method': '添加CSS变量定义或使用实际颜色值',
                        'var_name': var
                    })
                    
        # 检查缺少背景颜色
        if '.cyber-bg' in content or '.background' in content:
            if 'background-color' not in content:
                issues.append({
                    'type': 'missing_background_color',
                    'desc': '背景元素缺少background-color属性',
                    'severity': 'high',
                    'method': '添加明确的background-color属性'
                })
                
        return issues
        
    def check_js_issues(self, content: str, page_name: str) -> List[Dict]:
        """检查JavaScript问题"""
        issues = []
        
        # 检查缺少错误处理
        if 'function init()' in content or 'window.onload' in content:
            if 'try {' not in content and 'catch' not in content:
                issues.append({
                    'type': 'missing_error_handling',
                    'desc': '初始化函数缺少错误处理',
                    'severity': 'medium',
                    'method': '添加try-catch错误处理'
                })
                
        # 检查DOM元素访问
        dom_calls = re.findall(r'getElementById\([\'"]([^\'"]+)[\'"]\)', content)
        if dom_calls:
            # 检查这些元素是否在HTML中存在
            for elem_id in dom_calls[:5]:  # 只检查前5个
                if f'id="{elem_id}"' not in content and f"id='{elem_id}'" not in content:
                    issues.append({
                        'type': 'missing_dom_element',
                        'desc': f'JavaScript引用了不存在的元素: {elem_id}',
                        'severity': 'high',
                        'method': '添加对应的DOM元素或修正ID引用',
                        'element_id': elem_id
                    })
                    
        return issues
        
    def check_path_issues(self, content: str, page_name: str) -> List[Dict]:
        """检查路径问题"""
        issues = []
        
        # 检查相对路径
        bad_paths = [
            (r'href=["\']\.\./', 'parent_directory_path',
             '使用父目录相对路径可能导致404', 'medium'),
        ]
        
        for pattern, error_type, desc, severity in bad_paths:
            matches = re.findall(pattern, content)
            if matches:
                issues.append({
                    'type': error_type,
                    'desc': desc,
                    'severity': severity,
                    'method': '使用绝对路径或根路径'
                })
                
        return issues
        
    def fix_cdn_reference(self, content: str, issue: Dict) -> str:
        """修复CDN引用"""
        pattern = issue['pattern']
        replacement = issue['replacement']
        
        # 替换所有匹配的CDN链接
        new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        return new_content
        
    def fix_css_issue(self, content: str, issue: Dict) -> str:
        """修复CSS问题"""
        if issue['type'] == 'undefined_css_variable':
            # 添加CSS变量定义
            css_var = issue.get('var_name', 'undefined')
            
            # 在: root或body中添加变量定义
            if ':root {' in content:
                new_content = content.replace(
                    ':root {',
                    f':root {{\n    --{css_var}: #000000;'
                )
            elif 'body {' in content:
                new_content = content.replace(
                    'body {',
                    f'body {{\n    --{css_var}: #000000;'
                )
            else:
                new_content = content
                
            return new_content
            
        elif issue['type'] == 'missing_background_color':
            # 添加背景颜色
            if '.cyber-bg {' in content:
                new_content = content.replace(
                    '.cyber-bg {',
                    '.cyber-bg {\n    background-color: #0a0a0f;'
                )
            else:
                new_content = content
            return new_content
            
        return content
        
    def fix_js_issue(self, content: str, issue: Dict) -> str:
        """修复JavaScript问题"""
        if issue['type'] == 'missing_error_handling':
            # 添加try-catch
            if 'function init()' in content:
                new_content = content.replace(
                    'function init() {\n            createParticles();',
                    'function init() {\n            try {\n                createParticles();'
                )
                new_content = new_content.replace(
                    'setInterval(updateTime, 1000);\n        }',
                    'setInterval(updateTime, 1000);\n            } catch (e) {\n                console.error(\'初始化错误:\', e);\n            }\n        }'
                )
                return new_content
                
        elif issue['type'] == 'missing_dom_element':
            # 这个需要根据具体情况修复
            pass
            
        return content
        
    def scan_and_fix_page(self, page_path: str) -> Tuple[int, int]:
        """扫描并修复单个页面"""
        page_name = os.path.basename(page_path)
        errors_found = 0
        errors_fixed = 0
        
        try:
            with open(page_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # 执行各项检查
            cdn_issues = self.check_cdn_references(content, page_name)
            css_issues = self.check_css_issues(content, page_name)
            js_issues = self.check_js_issues(content, page_name)
            path_issues = self.check_path_issues(content, page_name)
            
            all_issues = cdn_issues + css_issues + js_issues + path_issues
            errors_found = len(all_issues)
            
            # 修复CDN问题
            for issue in cdn_issues:
                content = self.fix_cdn_reference(content, issue)
                self.log_fix(page_name, issue['type'], issue['desc'],
                           issue['method'], "CDN替换", "fixed",
                           issue['severity'], [page_path])
                errors_fixed += 1
                
            # 修复CSS问题
            for issue in css_issues:
                new_content = self.fix_css_issue(content, issue)
                if new_content != content:
                    content = new_content
                    self.log_fix(page_name, issue['type'], issue['desc'],
                               issue['method'], "CSS修复", "fixed",
                               issue['severity'], [page_path])
                    errors_fixed += 1
                else:
                    self.log_fix(page_name, issue['type'], issue['desc'],
                               issue['method'], "需要手动修复", "skipped",
                               issue['severity'], [page_path])
                    
            # 修复JS问题
            for issue in js_issues:
                new_content = self.fix_js_issue(content, issue)
                if new_content != content:
                    content = new_content
                    self.log_fix(page_name, issue['type'], issue['desc'],
                               issue['method'], "JS修复", "fixed",
                               issue['severity'], [page_path])
                    errors_fixed += 1
                else:
                    self.log_fix(page_name, issue['type'], issue['desc'],
                               issue['method'], "需要手动修复", "skipped",
                               issue['severity'], [page_path])
                    
            # 报告路径问题（不自动修复）
            for issue in path_issues:
                self.log_fix(page_name, issue['type'], issue['desc'],
                           issue['method'], "建议手动检查", "warning",
                           issue['severity'], [page_path])
                
            # 如果有修改，保存文件
            if content != original_content:
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            self.log_fix(page_name, 'file_error', str(e),
                       "文件处理失败", "error", "critical", [page_path])
            
        return errors_found, errors_fixed
        
    def run_comprehensive_scan(self):
        """运行全面扫描和修复"""
        start_time = datetime.now()
        
        print("=" * 70)
        print("🤖 全面系统修复AI员工 v2.0")
        print("=" * 70)
        print(f"\n📂 项目路径: {self.project_root}")
        print(f"📄 页面目录: {self.pages_dir}")
        print(f"👤 工程师: {self.employee_name}")
        print(f"🕐 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 扫描所有页面
        pages = self.scan_all_pages()
        print(f"\n📊 扫描配置:")
        print(f"   发现 {len(pages)} 个HTML页面")
        print(f"\n🔍 检测项目:")
        print(f"   1. CDN引用检查")
        print(f"   2. CSS问题检查")
        print(f"   3. JavaScript问题检查")
        print(f"   4. 路径问题检查")
        
        print(f"\n🔧 开始扫描和修复...\n")
        
        total_errors = 0
        total_fixed = 0
        
        for page_path in pages:
            page_name = os.path.basename(page_path)
            print(f"📄 扫描: {page_name}")
            
            errors, fixed = self.scan_and_fix_page(page_path)
            total_errors += errors
            total_fixed += fixed
            
        end_time = datetime.now()
        duration = end_time - start_time
        
        # 保存总结报告
        self.save_summary(total_errors, total_fixed, len(pages), duration)
        
        # 打印总结
        print("\n" + "=" * 70)
        print("📋 扫描修复总结报告")
        print("=" * 70)
        print(f"✅ 扫描页面数: {len(pages)}")
        print(f"⚠️  发现问题数: {total_errors}")
        print(f"🔧 已修复问题: {total_fixed}")
        print(f"⏱️  执行时间: {duration.total_seconds():.2f}秒")
        print("=" * 70)
        
        return total_errors, total_fixed, len(pages)
        
    def save_summary(self, total_errors: int, total_fixed: int,
                    pages_count: int, duration):
        """保存总结报告到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO fix_summary 
            (timestamp, total_pages_scanned, total_errors_found,
             total_errors_fixed, execution_time, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            pages_count,
            total_errors,
            total_fixed,
            str(duration),
            f"全面扫描{pages_count}个页面，发现{total_errors}个问题，修复{total_fixed}个"
        ))
        
        conn.commit()
        conn.close()
        
    def generate_detailed_report(self):
        """生成详细报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT page_name, error_type, error_description, 
                   fix_method, status, severity
            FROM comprehensive_fix_logs
            WHERE status = 'fixed'
            ORDER BY timestamp DESC
        ''')
        
        fixed_issues = cursor.fetchall()
        
        cursor.execute('''
            SELECT page_name, error_type, error_description, 
                   fix_method, status, severity
            FROM comprehensive_fix_logs
            WHERE status != 'fixed'
            ORDER BY timestamp DESC
        ''')
        
        other_issues = cursor.fetchall()
        
        conn.close()
        
        report = f"""
================================================================================
                    全面系统修复AI员工 - 详细报告
================================================================================
生成时间: {datetime.now().isoformat()}
工程师: {self.employee_name}

--------------------------------------------------------------------------------
                              已修复问题 ({len(fixed_issues)} 项)
--------------------------------------------------------------------------------
"""
        for issue in fixed_issues:
            report += f"""
页面: {issue[0]}
类型: {issue[1]}
描述: {issue[2]}
方法: {issue[3]}
严重度: {issue[5]}
"""
            
        if other_issues:
            report += f"""
--------------------------------------------------------------------------------
                              待处理问题 ({len(other_issues)} 项)
--------------------------------------------------------------------------------
"""
            for issue in other_issues:
                report += f"""
页面: {issue[0]}
类型: {issue[1]}
描述: {issue[2]}
方法: {issue[3]}
状态: {issue[4]}
严重度: {issue[5]}
"""
                
        report += """
================================================================================
                              修复方案总结
================================================================================

1. CDN引用优化
   - 将不稳定的cloudflare CDN替换为jsDelivr CDN
   - 提高资源加载稳定性

2. CSS变量规范化
   - 确保所有CSS变量在使用前已定义
   - 添加默认颜色值作为后备

3. JavaScript错误处理
   - 为关键初始化函数添加try-catch
   - 防止单点故障导致整个页面崩溃

4. DOM元素检查
   - 验证JavaScript引用的元素是否存在
   - 避免运行时错误

================================================================================
建议后续操作:
1. 在浏览器中测试所有修复的页面
2. 清除浏览器缓存
3. 检查页面功能是否正常
4. 如有问题，将相关页面反馈给AI员工进行二次修复

================================================================================
"""
        
        # 保存报告
        report_file = os.path.join(self.project_root, 'comprehensive_fix_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return report

def main():
    """主函数"""
    fixer = ComprehensiveFixAIEmployee()
    
    # 运行全面扫描
    errors, fixed, pages = fixer.run_comprehensive_scan()
    
    # 生成详细报告
    fixer.generate_detailed_report()
    
    return errors, fixed, pages

if __name__ == '__main__':
    main()