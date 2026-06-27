# -*- coding: utf-8 -*-
"""
AI员工：模板修复专家
负责批量检测和修复模板文件的依赖问题、静态文件缺失、路径配置错误等
"""

import os
import json
import logging
from datetime import datetime
from flask import render_template_string
import sqlite3

logger = logging.getLogger(__name__)

class TemplateFixerAI:
    """模板修复AI员工"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.employee_id = "template_fixer_001"
        self.employee_name = "模板修复专家"
        self.specialty = "模板依赖修复、静态文件缺失检测、路径配置优化"
        self.fix_count = 0
        self.report_count = 0
        
    def analyze_template_dependencies(self, template_dir):
        """分析模板依赖"""
        issues = []
        
        # 遍历所有模板文件
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    issues.extend(self._check_template_file(filepath))
        
        return issues
    
    def _check_template_file(self, filepath):
        """检查单个模板文件"""
        issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查静态文件依赖
            static_patterns = [
                ('url_for(\'static\', filename=', '静态文件引用'),
                ('href="/assets/', '静态资源链接'),
                ('src="/assets/', '静态资源链接'),
            ]
            
            for pattern, desc in static_patterns:
                if pattern in content:
                    # 提取文件名
                    import re
                    matches = re.findall(r'(?:filename=|href=|src=)"([^"]+)"', content)
                    for match in matches:
                        # 检查文件是否存在
                        static_path = os.path.join(os.path.dirname(filepath), '..', 'src', 'html', 'assets', match)
                        if not os.path.exists(static_path):
                            issues.append({
                                'type': 'static_file_missing',
                                'template': filepath,
                                'file': match,
                                'description': f'{desc}缺失: {match}',
                                'priority': 'high',
                                'auto_fix': True
                            })
            
            # 检查模板继承
            if 'extends' in content:
                import re
                parent_match = re.search(r'extends\s+"([^"]+)"', content)
                if parent_match:
                    parent_template = parent_match.group(1)
                    parent_path = os.path.join(os.path.dirname(filepath), parent_template)
                    if not os.path.exists(parent_path):
                        issues.append({
                            'type': 'parent_template_missing',
                            'template': filepath,
                            'file': parent_template,
                            'description': f'父模板缺失: {parent_template}',
                            'priority': 'high',
                            'auto_fix': False
                        })
        
        except Exception as e:
            logger.error(f"检查模板文件失败 {filepath}: {e}")
        
        return issues
    
    def auto_fix_template(self, template_path, issues):
        """自动修复模板问题"""
        fixed_issues = []
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 修复静态文件路径
            for issue in issues:
                if issue['type'] == 'static_file_missing' and issue['auto_fix']:
                    # 替换为存在的静态文件
                    missing_file = issue['file']
                    
                    # 如果CSS文件缺失，使用tailwind替代
                    if missing_file.endswith('.css'):
                        if 'style.css' in missing_file or 'mtscos-design-system.css' in missing_file:
                            # 替换为tailwind.min.css
                            content = content.replace(
                                f'url_for(\'static\', filename=\'{missing_file}\')',
                                'url_for(\'static\', filename=\'tailwind.min.css\')'
                            )
                            content = content.replace(
                                f'href="/assets/{missing_file}"',
                                'href="/assets/tailwind.min.css"'
                            )
                            fixed_issues.append({
                                'issue': issue,
                                'fix': f'替换为tailwind.min.css',
                                'timestamp': datetime.now().isoformat()
                            })
                            self.fix_count += 1
            
            # 如果内容有变化，保存修复后的文件
            if content != original_content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"模板修复成功: {template_path}")
        
        except Exception as e:
            logger.error(f"修复模板失败 {template_path}: {e}")
        
        return fixed_issues
    
    def batch_fix_templates(self, template_dir):
        """批量修复模板"""
        logger.info(f"[{self.employee_name}] 开始批量修复模板...")
        
        # 分析所有问题
        all_issues = self.analyze_template_dependencies(template_dir)
        
        logger.info(f"[{self.employee_name}] 发现 {len(all_issues)} 个问题")
        
        # 按优先级排序
        high_priority = [i for i in all_issues if i['priority'] == 'high']
        
        # 自动修复高优先级问题
        fixed_count = 0
        for issue in high_priority:
            if issue['auto_fix']:
                template_path = issue['template']
                template_issues = [i for i in all_issues if i['template'] == template_path]
                fixes = self.auto_fix_template(template_path, template_issues)
                if fixes:
                    fixed_count += len(fixes)
        
        logger.info(f"[{self.employee_name}] 成功修复 {fixed_count} 个问题")
        
        # 上报修复结果到数据库
        self.report_to_database(all_issues, fixed_count)
        
        return {
            'total_issues': len(all_issues),
            'fixed_count': fixed_count,
            'employee': self.employee_name,
            'specialty': self.specialty
        }
    
    def report_to_database(self, issues, fixed_count):
        """上报修复结果到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建AI员工修复报告表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_employee_fix_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                specialty TEXT,
                issue_type TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                fix_method TEXT,
                fixed BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                additional_info TEXT
            )
            ''')
            
            # 插入修复报告
            for issue in issues:
                cursor.execute('''
                INSERT INTO ai_employee_fix_reports 
                (employee_id, employee_name, specialty, issue_type, issue_description, fix_method, fixed, additional_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.employee_id,
                    self.employee_name,
                    self.specialty,
                    issue['type'],
                    issue['description'],
                    '自动修复' if issue['auto_fix'] else '需要人工处理',
                    issue['auto_fix'],
                    json.dumps(issue)
                ))
            
            conn.commit()
            conn.close()
            
            self.report_count += len(issues)
            logger.info(f"[{self.employee_name}] 已上报 {len(issues)} 个修复报告到数据库")
        
        except Exception as e:
            logger.error(f"[{self.employee_name}] 上报数据库失败: {e}")


def init_template_fixer_ai(db_path):
    """初始化模板修复AI员工"""
    return TemplateFixerAI(db_path)


# 创建全局实例
template_fixer_ai = None


def get_template_fixer_ai():
    """获取模板修复AI员工实例"""
    global template_fixer_ai
    if template_fixer_ai is None:
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        template_fixer_ai = TemplateFixerAI(db_path)
    return template_fixer_ai