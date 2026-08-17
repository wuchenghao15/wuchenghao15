# -*- coding: utf-8 -*-
"""
前端修复AI员工
负责修复super_admin_dashboard页面的前端问题，并上报数据库
"""

import json
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'


class FrontendFixerAI:
    """前端修复AI员工"""
    
    def __init__(self):
        self.employee_id = "frontend_fixer_001"
        self.name = "前端修复AI员工"
        self.role = "前端工程师"
        self.status = "active"
        self.fix_count = 0
        self.report_count = 0
        logger.info(f"[{self.employee_id}] 初始化前端修复AI员工")
    
    def create_fix_report_table(self):
        """创建修复报告表"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS frontend_fix_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                fix_type TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                affected_files TEXT,
                fix_details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"[{self.employee_id}] 修复报告表创建/验证成功")
            return True
        except Exception as e:
            logger.error(f"[{self.employee_id}] 创建修复报告表失败: {e}")
            return False
    
    def report_fix_to_db(self, fix_type, description, affected_files, fix_details):
        """上报修复结果到数据库"""
        try:
            self.create_fix_report_table()
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO frontend_fix_reports 
            (employee_id, employee_name, fix_type, description, status, affected_files, fix_details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.employee_id,
                self.name,
                fix_type,
                description,
                'completed',
                json.dumps(affected_files),
                json.dumps(fix_details)
            ))
            
            conn.commit()
            conn.close()
            self.report_count += 1
            logger.info(f"[{self.employee_id}] 修复报告已上报: {fix_type}")
            return True
        except Exception as e:
            logger.error(f"[{self.employee_id}] 上报修复报告失败: {e}")
            return False
    
    def analyze_template(self, template_path):
        """分析模板文件，找出需要修复的问题"""
        issues = []
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查Google Fonts引用
            if 'fonts.googleapis.com' in content:
                issues.append({
                    'type': 'external_dependency',
                    'description': '使用了外部Google Fonts CDN，可能加载失败',
                    'severity': 'high'
                })
            
            # 检查外部API调用
            if 'api.ipify.org' in content:
                issues.append({
                    'type': 'external_api',
                    'description': '使用了外部IP获取API，可能失败',
                    'severity': 'high'
                })
            
            # 检查静态数据
            if "'--'" in content or 'text: "--"' in content:
                issues.append({
                    'type': 'static_data',
                    'description': '页面包含静态占位符数据，应加载真实数据',
                    'severity': 'medium'
                })
            
            # 检查CSS加载
            if 'src/html/assets' not in content:
                issues.append({
                    'type': 'css_missing',
                    'description': '可能缺少CSS文件引用',
                    'severity': 'medium'
                })
            
            logger.info(f"[{self.employee_id}] 分析模板 {template_path}，发现 {len(issues)} 个问题")
            return issues
            
        except Exception as e:
            logger.error(f"[{self.employee_id}] 分析模板失败: {e}")
            return []
    
    def fix_template(self, template_path):
        """修复模板文件"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fixes_applied = []
            
            # 修复1: 替换Google Fonts为系统字体
            if 'fonts.googleapis.com' in content:
                content = content.replace(
                    '<link rel="preconnect" href="https://fonts.googleapis.com">\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">',
                    '<style>\n        body {\n            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;\n        }\n    </style>'
                )
                fixes_applied.append('替换Google Fonts为系统字体')
            
            # 修复2: 替换外部IP API为本地API
            if 'api.ipify.org' in content:
                content = content.replace(
                    'https://api.ipify.org?format=json',
                    '/api/user/ip'
                )
                fixes_applied.append('替换外部IP API为本地API')
            
            # 修复3: 添加实时数据加载脚本
            if 'loadDashboardData' not in content:
                load_script = '''
<script>
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

function loadDashboardData() {
    fetch('/api/admin/dashboard_stats')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById('user-count').textContent = data.data.user_count;
                document.getElementById('active-users').textContent = '今日活跃: ' + data.data.active_users;
                document.getElementById('route-count').textContent = data.data.route_count;
                document.getElementById('system-status').textContent = data.data.system_status;
            }
        })
        .catch(err => console.warn('统计数据加载失败:', err));
}
</script>
'''
                content = content.replace('</body>', load_script + '</body>')
                fixes_applied.append('添加实时数据加载脚本')
            
            # 保存修复后的文件
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.fix_count += len(fixes_applied)
            logger.info(f"[{self.employee_id}] 模板修复完成，应用了 {len(fixes_applied)} 个修复")
            return fixes_applied
            
        except Exception as e:
            logger.error(f"[{self.employee_id}] 修复模板失败: {e}")
            return []
    
    def run_complete_fix(self):
        """执行完整修复流程"""
        logger.info(f"[{self.employee_id}] 开始执行前端修复任务...")
        
        template_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/templates/super_admin_dashboard.html'
        
        # 分析问题
        issues = self.analyze_template(template_path)
        logger.info(f"[{self.employee_id}] 发现 {len(issues)} 个问题")
        
        # 修复问题
        fixes = self.fix_template(template_path)
        
        # 上报数据库
        for fix in fixes:
            self.report_fix_to_db(
                fix_type='template_fix',
                description=fix,
                affected_files=[template_path],
                fix_details={'issue_count': len(issues), 'fix_applied': fixes}
            )
        
        # 修复base_layout.html
        base_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/templates/base_layout.html'
        base_fixes = self.fix_template(base_path)
        
        for fix in base_fixes:
            self.report_fix_to_db(
                fix_type='base_layout_fix',
                description=fix,
                affected_files=[base_path],
                fix_details={'fix_applied': base_fixes}
            )
        
        result = {
            'employee_id': self.employee_id,
            'employee_name': self.name,
            'issues_found': len(issues),
            'fixes_applied': self.fix_count,
            'reports_submitted': self.report_count,
            'status': 'completed',
            'timestamp': '2026-06-27 21:20:00'
        }
        
        logger.info(f"[{self.employee_id}] 前端修复任务完成: {json.dumps(result, indent=2)}")
        return result


# 创建全局实例
frontend_fixer_ai = FrontendFixerAI()


def run_frontend_fix():
    """执行前端修复"""
    return frontend_fixer_ai.run_complete_fix()


if __name__ == '__main__':
    result = run_frontend_fix()
    print(json.dumps(result, ensure_ascii=False, indent=2))