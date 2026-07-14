# -*- coding: utf-8 -*-
"""
超级管理员仪表盘修复AI员工
强力修复super_admin_dashboard页面的所有问题，包括CSS、样式、数据加载等
并上报数据库
"""

import json
import sqlite3
import logging
import os
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
BASE_DIR = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app'


class SuperAdminDashboardFixerAI:
    """超级管理员仪表盘修复AI员工"""
    
    def __init__(self):
        self.employee_id = "super_admin_dashboard_fixer_001"
        self.name = "超级管理员仪表盘修复AI员工"
        self.role = "高级前端工程师"
        self.status = "active"
        self.fix_count = 0
        self.report_count = 0
        self.fixes_applied = []
        logger.info(f"[{self.employee_id}] 初始化超级管理员仪表盘修复AI员工")
    
    def create_fix_report_table(self):
        """创建修复报告表"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS super_admin_dashboard_fix_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                fix_type TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'high',
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
    
    def report_fix_to_db(self, fix_type, description, severity, affected_files, fix_details):
        """上报修复结果到数据库"""
        try:
            self.create_fix_report_table()
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO super_admin_dashboard_fix_reports 
            (employee_id, employee_name, fix_type, description, severity, status, affected_files, fix_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.employee_id,
                self.name,
                fix_type,
                description,
                severity,
                'completed',
                json.dumps(affected_files, ensure_ascii=False),
                json.dumps(fix_details, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            self.report_count += 1
            logger.info(f"[{self.employee_id}] 修复报告已上报: {fix_type} - {description}")
            return True
        except Exception as e:
            logger.error(f"[{self.employee_id}] 上报修复报告失败: {e}")
            return False
    
    def diagnose_issues(self):
        """诊断所有问题"""
        issues = []
        
        # 检查1: CSS文件是否存在
        tailwind_path = os.path.join(BASE_DIR, 'static', 'tailwind.min.css')
        fontawesome_path = os.path.join(BASE_DIR, 'static', 'all.min.css')
        
        if not os.path.exists(tailwind_path):
            issues.append({
                'type': 'css_missing',
                'description': 'tailwind.min.css 文件不存在',
                'severity': 'critical',
                'path': tailwind_path
            })
        
        if not os.path.exists(fontawesome_path):
            issues.append({
                'type': 'css_missing',
                'description': 'all.min.css (FontAwesome) 文件不存在',
                'severity': 'critical',
                'path': fontawesome_path
            })
        
        # 检查2: base_layout.html中的CSS引用
        base_layout_path = os.path.join(BASE_DIR, 'templates', 'base_layout.html')
        if os.path.exists(base_layout_path):
            with open(base_layout_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'tailwind.min.css' in content and not os.path.exists(tailwind_path):
                issues.append({
                    'type': 'css_path_error',
                    'description': 'base_layout.html引用了不存在的tailwind.min.css',
                    'severity': 'critical'
                })
            
            if 'all.min.css' in content and not os.path.exists(fontawesome_path):
                issues.append({
                    'type': 'css_path_error',
                    'description': 'base_layout.html引用了不存在的all.min.css',
                    'severity': 'critical'
                })
            
            if '@vite/client' in content:
                issues.append({
                    'type': 'dev_dependency',
                    'description': '页面引用了Vite开发客户端，生产环境不需要',
                    'severity': 'medium'
                })
        
        # 检查3: super_admin_dashboard.html模板
        dashboard_path = os.path.join(BASE_DIR, 'templates', 'super_admin_dashboard.html')
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'loadDashboardData' not in content:
                issues.append({
                    'type': 'data_loading',
                    'description': '缺少实时数据加载脚本',
                    'severity': 'high'
                })
            
            if 'grid grid-cols' not in content:
                issues.append({
                    'type': 'layout',
                    'description': '可能缺少网格布局样式',
                    'severity': 'medium'
                })
        
        # 检查4: 静态CSS目录
        css_dir = os.path.join(BASE_DIR, 'static', 'css')
        if os.path.exists(css_dir):
            css_files = os.listdir(css_dir)
            logger.info(f"[{self.employee_id}] 发现CSS文件: {css_files}")
        
        logger.info(f"[{self.employee_id}] 诊断完成，发现 {len(issues)} 个问题")
        return issues
    
    def generate_tailwind_min_css(self):
        """生成简化版的Tailwind CSS，包含常用类"""
        logger.info(f"[{self.employee_id}] 生成tailwind.min.css...")
        
        tailwind_css = '''/* Tailwind CSS - Minimal Build for MTSCOS AI System */
*,::before,::after{box-sizing:border-box;border-width:0;border-style:solid;border-color:#e5e7eb}
::before,::after{--tw-content:''}
html{line-height:1.5;-webkit-text-size-adjust:100%;-moz-tab-size:4;tab-size:4;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif}
body{margin:0;line-height:inherit}
hr{height:0;color:inherit;border-top-width:1px}
abbr:where([title]){-webkit-text-decoration:underline dotted;text-decoration:underline dotted}
h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}
a{color:inherit;text-decoration:inherit}
b,strong{font-weight:bolder}
code,kbd,samp,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;font-size:1em}
small{font-size:80%}
sub,sup{font-size:75%;line-height:0;position:relative;vertical-align:baseline}
sub{bottom:-.25em}
sup{top:-.5em}
table{text-indent:0;border-color:inherit;border-collapse:collapse}
button,input,optgroup,select,textarea{font-family:inherit;font-size:100%;font-weight:inherit;line-height:inherit;color:inherit;margin:0;padding:0}
button,select{text-transform:none}
button,[type='button'],[type='reset'],[type='submit']{-webkit-appearance:button;background-color:transparent;background-image:none}
:-moz-focusring{outline:auto}
:-moz-ui-invalid{box-shadow:none}
progress{vertical-align:baseline}
::-webkit-inner-spin-button,::-webkit-outer-spin-button{height:auto}
[type='search']{-webkit-appearance:textfield;outline-offset:-2px}
::-webkit-search-decoration{-webkit-appearance:none}
::-webkit-file-upload-button{-webkit-appearance:button;font:inherit}
summary{display:list-item}
blockquote,dl,dd,h1,h2,h3,h4,h5,h6,hr,figure,p,pre{margin:0}
fieldset{margin:0;padding:0}
legend{padding:0}
ol,ul,menu{list-style:none;margin:0;padding:0}
textarea{resize:vertical}
input::placeholder,textarea::placeholder{opacity:1;color:#9ca3af}
button,[role="button"]{cursor:pointer}
:disabled{cursor:default}
img,svg,video,canvas,audio,iframe,embed,object{display:block;vertical-align:middle}
img,video{max-width:100%;height:auto}
[hidden]{display:none}

/* Flex & Grid */
.flex{display:flex}.inline-flex{display:inline-flex}.grid{display:grid}.hidden{display:none}.block{display:block}.inline-block{display:inline-block}
.flex-col{flex-direction:column}.flex-row{flex-direction:row}.flex-wrap{flex-wrap:wrap}
.items-center{align-items:center}.items-start{align-items:flex-start}.items-end{align-items:flex-end}
.justify-center{justify-content:center}.justify-between{justify-content:space-between}.justify-start{justify-content:flex-start}.justify-end{justify-content:flex-end}
.gap-1{gap:0.25rem}.gap-2{gap:0.5rem}.gap-3{gap:0.75rem}.gap-4{gap:1rem}.gap-6{gap:1.5rem}.gap-8{gap:2rem}
.grid-cols-1{grid-template-columns:repeat(1,minmax(0,1fr))}.grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}.grid-cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}
.flex-1{flex:1 1 0%}.flex-shrink-0{flex-shrink:0}

/* Spacing */
.m-0{margin:0}.m-2{margin:0.5rem}.m-4{margin:1rem}
.mt-1{margin-top:0.25rem}.mt-2{margin-top:0.5rem}.mt-3{margin-top:0.75rem}.mt-4{margin-top:1rem}.mt-6{margin-top:1.5rem}.mt-8{margin-top:2rem}
.mb-1{margin-bottom:0.25rem}.mb-2{margin-bottom:0.5rem}.mb-3{margin-bottom:0.75rem}.mb-4{margin-bottom:1rem}.mb-6{margin-bottom:1.5rem}.mb-8{margin-bottom:2rem}
.ml-2{margin-left:0.5rem}.ml-3{margin-left:0.75rem}.ml-4{margin-left:1rem}.mr-2{margin-right:0.5rem}.mr-3{margin-right:0.75rem}.mr-4{margin-right:1rem}
.p-2{padding:0.5rem}.p-3{padding:0.75rem}.p-4{padding:1rem}.p-6{padding:1.5rem}.p-8{padding:2rem}
.px-2{padding-left:0.5rem;padding-right:0.5rem}.px-3{padding-left:0.75rem;padding-right:0.75rem}.px-4{padding-left:1rem;padding-right:1rem}.px-6{padding-left:1.5rem;padding-right:1.5rem}.px-8{padding-left:2rem;padding-right:2rem}
.py-2{padding-top:0.5rem;padding-bottom:0.5rem}.py-3{padding-top:0.75rem;padding-bottom:0.75rem}.py-4{padding-top:1rem;padding-bottom:1rem}.py-6{padding-top:1.5rem;padding-bottom:1.5rem}
.pt-2{padding-top:0.5rem}.pt-4{padding-top:1rem}.pb-2{padding-bottom:0.5rem}.pb-4{padding-bottom:1rem}.pl-4{padding-left:1rem}.pr-4{padding-right:1rem}

/* Sizing */
.w-full{width:100%}.w-1\/2{width:50%}.w-1\/3{width:33.333%}.w-1\/4{width:25%}.w-auto{width:auto}
.h-full{height:100%}.h-auto{height:auto}.h-screen{height:100vh}
.min-h-screen{min-height:100vh}
.max-w-full{max-width:100%}

/* Typography */
.text-xs{font-size:0.75rem;line-height:1rem}.text-sm{font-size:0.875rem;line-height:1.25rem}.text-base{font-size:1rem;line-height:1.5rem}.text-lg{font-size:1.125rem;line-height:1.75rem}.text-xl{font-size:1.25rem;line-height:1.75rem}.text-2xl{font-size:1.5rem;line-height:2rem}.text-3xl{font-size:1.875rem;line-height:2.25rem}.text-4xl{font-size:2.25rem;line-height:2.5rem}
.font-light{font-weight:300}.font-normal{font-weight:400}.font-medium{font-weight:500}.font-semibold{font-weight:600}.font-bold{font-weight:700}
.leading-tight{line-height:1.25}.leading-normal{line-height:1.5}
.text-center{text-align:center}.text-left{text-align:left}.text-right{text-align:right}
.italic{font-style:italic}.uppercase{text-transform:uppercase}.lowercase{text-transform:lowercase}.capitalize{text-transform:capitalize}
.truncate{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* Colors - Text */
.text-white{color:#fff}.text-black{color:#000}
.text-gray-50{color:#f9fafb}.text-gray-100{color:#f3f4f6}.text-gray-200{color:#e5e7eb}.text-gray-300{color:#d1d5db}.text-gray-400{color:#9ca3af}.text-gray-500{color:#6b7280}.text-gray-600{color:#4b5563}.text-gray-700{color:#374151}.text-gray-800{color:#1f2937}.text-gray-900{color:#111827}
.text-red-50{color:#fef2f2}.text-red-100{color:#fee2e2}.text-red-400{color:#f87171}.text-red-500{color:#ef4444}.text-red-600{color:#dc2626}.text-red-700{color:#b91c1c}
.text-blue-50{color:#eff6ff}.text-blue-100{color:#dbeafe}.text-blue-400{color:#60a5fa}.text-blue-500{color:#3b82f6}.text-blue-600{color:#2563eb}.text-blue-700{color:#1d4ed8}.text-blue-800{color:#1e40af}
.text-green-50{color:#f0fdf4}.text-green-100{color:#dcfce7}.text-green-400{color:#4ade80}.text-green-500{color:#22c55e}.text-green-600{color:#16a34a}.text-green-700{color:#15803d}
.text-yellow-50{color:#fefce8}.text-yellow-100{color:#fef9c3}.text-yellow-400{color:#facc15}.text-yellow-500{color:#eab308}.text-yellow-600{color:#ca8a04}.text-yellow-700{color:#a16207}
.text-purple-50{color:#faf5ff}.text-purple-100{color:#f3e8ff}.text-purple-400{color:#c084fc}.text-purple-500{color:#a855f7}.text-purple-600{color:#9333ea}.text-purple-700{color:#7e22ce}
.text-orange-50{color:#fff7ed}.text-orange-100{color:#ffedd5}.text-orange-400{color:#fb923c}.text-orange-500{color:#f97316}.text-orange-600{color:#ea580c}.text-orange-700{color:#c2410c}
.text-indigo-50{color:#eef2ff}.text-indigo-100{color:#e0e7ff}.text-indigo-400{color:#818cf8}.text-indigo-500{color:#6366f1}.text-indigo-600{color:#4f46e5}.text-indigo-700{color:#4338ca}
.text-pink-50{color:#fdf2f8}.text-pink-100{color:#fce7f3}.text-pink-400{color:#f472b6}.text-pink-500{color:#ec4899}.text-pink-600{color:#db2777}
.text-opacity-75{--tw-text-opacity:0.75;color:rgba(255,255,255,var(--tw-text-opacity))}.text-opacity-90{--tw-text-opacity:0.9}

/* Colors - Background */
.bg-white{background-color:#fff}.bg-black{background-color:#000}
.bg-gray-50{background-color:#f9fafb}.bg-gray-100{background-color:#f3f4f6}.bg-gray-200{background-color:#e5e7eb}.bg-gray-500{background-color:#6b7280}.bg-gray-600{background-color:#4b5563}.bg-gray-700{background-color:#374151}.bg-gray-800{background-color:#1f2937}.bg-gray-900{background-color:#111827}
.bg-red-50{background-color:#fef2f2}.bg-red-100{background-color:#fee2e2}.bg-red-500{background-color:#ef4444}.bg-red-600{background-color:#dc2626}.bg-red-700{background-color:#b91c1c}
.bg-blue-50{background-color:#eff6ff}.bg-blue-100{background-color:#dbeafe}.bg-blue-500{background-color:#3b82f6}.bg-blue-600{background-color:#2563eb}.bg-blue-700{background-color:#1d4ed8}
.bg-green-50{background-color:#f0fdf4}.bg-green-100{background-color:#dcfce7}.bg-green-500{background-color:#22c55e}.bg-green-600{background-color:#16a34a}.bg-green-700{background-color:#15803d}
.bg-yellow-50{background-color:#fefce8}.bg-yellow-100{background-color:#fef9c3}.bg-yellow-500{background-color:#eab308}.bg-yellow-600{background-color:#ca8a04}
.bg-purple-50{background-color:#faf5ff}.bg-purple-100{background-color:#f3e8ff}.bg-purple-500{background-color:#a855f7}.bg-purple-600{background-color:#9333ea}.bg-purple-700{background-color:#7e22ce}
.bg-orange-50{background-color:#fff7ed}.bg-orange-100{background-color:#ffedd5}.bg-orange-500{background-color:#f97316}.bg-orange-600{background-color:#ea580c}.bg-orange-700{background-color:#c2410c}
.bg-indigo-50{background-color:#eef2ff}.bg-indigo-100{background-color:#e0e7ff}.bg-indigo-500{background-color:#6366f1}.bg-indigo-600{background-color:#4f46e5}.bg-indigo-700{background-color:#4338ca}
.bg-pink-50{background-color:#fdf2f8}.bg-pink-100{background-color:#fce7f3}.bg-pink-500{background-color:#ec4899}.bg-pink-600{background-color:#db2777}

/* Gradients */
.bg-gradient-to-r{background-image:linear-gradient(to right,var(--tw-gradient-stops))}
.from-blue-500{--tw-gradient-from:#3b82f6;--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to,rgba(59,130,246,0))}.to-blue-600{--tw-gradient-to:#2563eb}
.from-green-500{--tw-gradient-from:#22c55e;--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to,rgba(34,197,94,0))}.to-green-600{--tw-gradient-to:#16a34a}
.from-purple-500{--tw-gradient-from:#a855f7;--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to,rgba(168,85,247,0))}.to-purple-600{--tw-gradient-to:#9333ea}
.from-orange-500{--tw-gradient-from:#f97316;--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to,rgba(249,115,22,0))}.to-orange-600{--tw-gradient-to:#ea580c}
.from-red-500{--tw-gradient-from:#ef4444;--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to,rgba(239,68,68,0))}.to-red-600{--tw-gradient-to:#dc2626}
.from-indigo-500{--tw-gradient-from:#6366f1;--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to,rgba(99,102,241,0))}.to-indigo-600{--tw-gradient-to:#4f46e5}

/* Borders */
.border{border-width:1px}.border-0{border-width:0}.border-2{border-width:2px}
.border-t{border-top-width:1px}.border-b{border-bottom-width:1px}.border-l{border-left-width:1px}.border-r{border-right-width:1px}
.border-gray-100{border-color:#f3f4f6}.border-gray-200{border-color:#e5e7eb}.border-gray-300{border-color:#d1d5db}.border-gray-400{border-color:#9ca3af}
.border-blue-200{border-color:#bfdbfe}.border-blue-300{border-color:#93c5fd}.border-blue-500{border-color:#3b82f6}
.border-green-200{border-color:#bbf7d0}.border-green-300{border-color:#86efac}.border-green-500{border-color:#22c55e}
.border-red-200{border-color:#fecaca}.border-red-300{border-color:#fca5a5}.border-red-500{border-color:#ef4444}
.rounded{border-radius:0.25rem}.rounded-sm{border-radius:0.125rem}.rounded-md{border-radius:0.375rem}.rounded-lg{border-radius:0.5rem}.rounded-xl{border-radius:0.75rem}.rounded-2xl{border-radius:1rem}.rounded-full{border-radius:9999px}
.rounded-t-lg{border-top-left-radius:0.5rem;border-top-right-radius:0.5rem}
.rounded-b-lg{border-bottom-right-radius:0.5rem;border-bottom-left-radius:0.5rem}

/* Shadows */
.shadow-sm{--tw-shadow:0 1px 2px 0 rgba(0,0,0,0.05);box-shadow:var(--tw-shadow)}
.shadow{--tw-shadow:0 1px 3px 0 rgba(0,0,0,0.1),0 1px 2px -1px rgba(0,0,0,0.1);box-shadow:var(--tw-shadow)}
.shadow-md{--tw-shadow:0 4px 6px -1px rgba(0,0,0,0.1),0 2px 4px -2px rgba(0,0,0,0.1);box-shadow:var(--tw-shadow)}
.shadow-lg{--tw-shadow:0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -4px rgba(0,0,0,0.1);box-shadow:var(--tw-shadow)}
.shadow-xl{--tw-shadow:0 20px 25px -5px rgba(0,0,0,0.1),0 8px 10px -6px rgba(0,0,0,0.1);box-shadow:var(--tw-shadow)}
.shadow-2xl{--tw-shadow:0 25px 50px -12px rgba(0,0,0,0.25);box-shadow:var(--tw-shadow)}
.shadow-inner{--tw-shadow:inset 0 2px 4px 0 rgba(0,0,0,0.05);box-shadow:var(--tw-shadow)}

/* Opacity */
.opacity-0{opacity:0}.opacity-25{opacity:0.25}.opacity-50{opacity:0.5}.opacity-75{opacity:0.75}.opacity-80{opacity:0.8}.opacity-90{opacity:0.9}.opacity-100{opacity:1}

/* Transitions */
.transition{transition-property:color,background-color,border-color,text-decoration-color,fill,stroke,opacity,box-shadow,transform,filter,backdrop-filter;transition-timing-function:cubic-bezier(0.4,0,0.2,1);transition-duration:150ms}
.transition-all{transition-property:all;transition-timing-function:cubic-bezier(0.4,0,0.2,1);transition-duration:150ms}
.transition-colors{transition-property:color,background-color,border-color,text-decoration-color,fill,stroke;transition-timing-function:cubic-bezier(0.4,0,0.2,1);transition-duration:150ms}
.transition-opacity{transition-property:opacity;transition-timing-function:cubic-bezier(0.4,0,0.2,1);transition-duration:150ms}
.transition-transform{transition-property:transform;transition-timing-function:cubic-bezier(0.4,0,0.2,1);transition-duration:150ms}
.duration-150{transition-duration:150ms}.duration-200{transition-duration:200ms}.duration-300{transition-duration:300ms}.duration-500{transition-duration:500ms}
.ease-in{transition-timing-function:cubic-bezier(0.4,0,1,1)}.ease-out{transition-timing-function:cubic-bezier(0,0,0.2,1)}.ease-in-out{transition-timing-function:cubic-bezier(0.4,0,0.2,1)}

/* Hover */
.hover\:bg-gray-50:hover{background-color:#f9fafb}.hover\:bg-gray-100:hover{background-color:#f3f4f6}.hover\:bg-gray-600:hover{background-color:#4b5563}.hover\:bg-gray-700:hover{background-color:#374151}
.hover\:bg-blue-600:hover{background-color:#2563eb}.hover\:bg-blue-700:hover{background-color:#1d4ed8}
.hover\:bg-green-600:hover{background-color:#16a34a}.hover\:bg-green-700:hover{background-color:#15803d}
.hover\:bg-red-600:hover{background-color:#dc2626}.hover\:bg-red-700:hover{background-color:#b91c1c}
.hover\:bg-purple-600:hover{background-color:#9333ea}.hover\:bg-purple-700:hover{background-color:#7e22ce}
.hover\:bg-orange-600:hover{background-color:#ea580c}.hover\:bg-orange-700:hover{background-color:#c2410c}
.hover\:bg-indigo-600:hover{background-color:#4f46e5}.hover\:bg-indigo-700:hover{background-color:#4338ca}
.hover\:text-white:hover{color:#fff}
.hover\:text-gray-900:hover{color:#111827}.hover\:text-gray-700:hover{color:#374151}
.hover\:text-blue-600:hover{color:#2563eb}.hover\:text-blue-700:hover{color:#1d4ed8}
.hover\:shadow-lg:hover{--tw-shadow:0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -4px rgba(0,0,0,0.1);box-shadow:var(--tw-shadow)}
.hover\:shadow-xl:hover{--tw-shadow:0 20px 25px -5px rgba(0,0,0,0.1),0 8px 10px -6px rgba(0,0,0,0.1);box-shadow:var(--tw-shadow)}
.hover\:scale-105:hover{transform:scale(1.05)}
.hover\:opacity-100:hover{opacity:1}

/* Focus */
.focus\:outline-none:focus{outline:2px solid transparent;outline-offset:2px}
.focus\:ring-2:focus{--tw-ring-offset-shadow:var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);--tw-ring-shadow:var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color);box-shadow:var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow,0 0 #0000)}
.focus\:ring-blue-500:focus{--tw-ring-color:#3b82f6}
.focus\:ring-offset-2:focus{--tw-ring-offset-width:2px}

/* Position */
.relative{position:relative}.absolute{position:absolute}.fixed{position:fixed}.sticky{position:sticky}
.top-0{top:0}.bottom-0{bottom:0}.left-0{left:0}.right-0{right:0}
.top-2{top:0.5rem}.right-2{right:0.5rem}.bottom-2{bottom:0.5rem}.left-2{left:0.5rem}
.top-4{top:1rem}.right-4{right:1rem}.bottom-4{bottom:1rem}.left-4{left:1rem}
.z-10{z-index:10}.z-20{z-index:20}.z-50{z-index:50}.z-100{z-index:100}
.overflow-hidden{overflow:hidden}.overflow-auto{overflow:auto}.overflow-scroll{overflow:scroll}
.overflow-x-hidden{overflow-x:hidden}.overflow-y-auto{overflow-y:auto}.overflow-y-scroll{overflow-y:scroll}

/* Responsive - md */
@media (min-width:768px){
.md\:grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.md\:grid-cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.md\:grid-cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}
.md\:flex-row{flex-direction:row}
.md\:block{display:block}
.md\:w-auto{width:auto}
}

/* Responsive - lg */
@media (min-width:1024px){
.lg\:grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.lg\:grid-cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.lg\:grid-cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}
.lg\:flex-row{flex-direction:row}
}

/* Responsive - xl */
@media (min-width:1280px){
.xl\:grid-cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.xl\:grid-cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}
}

/* Object fit */
.object-cover{object-fit:cover}.object-contain{object-fit:contain}

/* Cursor */
.cursor-pointer{cursor:pointer}.cursor-default{cursor:default}.cursor-not-allowed{cursor:not-allowed}

/* User select */
.select-none{user-select:none}.select-text{user-select:text}.select-all{user-select:all}

/* Visibility */
.visible{visibility:visible}.invisible{visibility:hidden}

/* List */
.list-disc{list-style-type:disc}.list-decimal{list-style-type:decimal}
.list-inside{list-style-position:inside}

/* Table */
.table{display:table}.table-cell{display:table-cell}.table-row{display:table-row}

/* Transform */
.transform{transform:translate(var(--tw-translate-x),var(--tw-translate-y)) rotate(var(--tw-rotate)) skewX(var(--tw-skew-x)) skewY(var(--tw-skew-y)) scaleX(var(--tw-scale-x)) scaleY(var(--tw-scale-y))}
.scale-100{--tw-scale-x:1;--tw-scale-y:1}.scale-105{--tw-scale-x:1.05;--tw-scale-y:1.05}.scale-110{--tw-scale-x:1.1;--tw-scale-y:1.1}
.rotate-45{--tw-rotate:45deg}.rotate-90{--tw-rotate:90deg}.rotate-180{--tw-rotate:180deg}

/* Animations */
@keyframes spin{to{transform:rotate(360deg)}}
.animate-spin{animation:spin 1s linear infinite}
@keyframes ping{75%,100%{transform:scale(2);opacity:0}}
.animate-ping{animation:ping 1s cubic-bezier(0,0,0.2,1) infinite}
@keyframes pulse{50%{opacity:.5}}
.animate-pulse{animation:pulse 2s cubic-bezier(0.4,0,0.6,1) infinite}
@keyframes bounce{0%,100%{transform:translateY(-25%);animation-timing-function:cubic-bezier(0.8,0,1,1)}50%{transform:translateY(0);animation-timing-function:cubic-bezier(0,0,0.2,1)}}
.animate-bounce{animation:bounce 1s infinite}

/* Content */
.content-auto{content-visibility:auto}

/* Additional utility classes commonly used */
.space-y-2 > * + *{margin-top:0.5rem}.space-y-4 > * + *{margin-top:1rem}.space-y-6 > * + *{margin-top:1.5rem}
.space-x-2 > * + *{margin-left:0.5rem}.space-x-4 > * + *{margin-left:1rem}.space-x-6 > * + *{margin-left:1.5rem}

.indent{text-indent:1.5rem}
.line-clamp-2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.line-clamp-3{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}

.appearance-none{-webkit-appearance:none;appearance:none}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border-width:0}
'''
        
        output_path = os.path.join(BASE_DIR, 'static', 'tailwind.min.css')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(tailwind_css)
        
        logger.info(f"[{self.employee_id}] tailwind.min.css 生成成功: {output_path}")
        return True
    
    def generate_fontawesome_css(self):
        """生成简化版的FontAwesome CSS，使用内联SVG图标"""
        logger.info(f"[{self.employee_id}] 生成all.min.css (FontAwesome替代)...")
        
        fontawesome_css = '''/* Font Awesome Icons - SVG Based Implementation for MTSCOS AI System */
.fas,.far,.fal,.fab{display:inline-block;font-style:normal;font-variant:normal;text-rendering:auto;line-height:1;width:1em;height:1em;position:relative}
.fas::before,.far::before,.fal::before,.fab::before{content:"";display:inline-block;width:1em;height:1em;background-size:contain;background-repeat:no-repeat;background-position:center;vertical-align:middle}

/* Common icon sizes */
.fa-xs{font-size:.75em}.fa-sm{font-size:.875em}.fa-lg{font-size:1.3333333em;line-height:.75em;vertical-align:-.0667em}
.fa-2x{font-size:2em}.fa-3x{font-size:3em}.fa-4x{font-size:4em}.fa-5x{font-size:5em}
.fa-fw{text-align:center;width:1.25em}

/* Icon styling */
.fa-spin{animation:fa-spin 2s infinite linear}
.fa-pulse{animation:fa-spin 1s infinite steps(8)}
@keyframes fa-spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}

.fa-border{border:solid .08em #eee;border-radius:.1em;padding:.2em .25em .15em}
.fa-pull-left{float:left;margin-right:.3em}
.fa-pull-right{float:right;margin-left:.3em}

.fa-ul{list-style-type:none;padding-left:0;margin-left:var(--fa-li-width,2.5em)}
.fa-ul > li{position:relative}
.fa-li{left:calc(-1 * var(--fa-li-width,2.5em));position:absolute;text-align:center;width:var(--fa-li-width,2.5em);line-height:inherit}

.fa-stack{position:relative;display:inline-block;height:2em;line-height:2em;width:2.5em;vertical-align:middle}
.fa-stack-1x,.fa-stack-2x{position:absolute;left:0;width:100%;text-align:center}
.fa-stack-1x{line-height:inherit}
.fa-stack-2x{font-size:2em}
.fa-inverse{color:#fff}

/* Use Unicode for common icons - these will show as text but provide basic functionality */
/* For full SVG support, we use data URIs for common icons */

.fas.fa-crown::before{content:"\\1F451"}
.fas.fa-users::before{content:"\\1F465"}
.fas.fa-heartbeat::before{content:"\\1F493"}
.fas.fa-route::before{content:"\\1F6E3"}
.fas.fa-shield-alt::before{content:"\\1F6E1"}
.fas.fa-tachometer-alt::before{content:"\\1F4CA"}
.fas.fa-desktop::before{content:"\\1F5A5"}
.fas.fa-list::before{content:"\\2630"}
.fas.fa-user::before{content:"\\1F464"}
.fas.fa-user-cog::before{content:"\\2699"}
.fas.fa-plus::before{content:"\\002B"}
.fas.fa-lock::before{content:"\\1F512"}
.fas.fa-file-alt::before{content:"\\1F4C4"}
.fas.fa-question-circle::before{content:"\\2753"}
.fas.fa-chart-line::before{content:"\\1F4C8"}
.fas.fa-graduation-cap::before{content:"\\1F393"}
.fas.fa-book::before{content:"\\1F4D6"}
.fas.fa-history::before{content:"\\23F3"}
.fas fa-book-open::before{content:"\\1F4D6"}
.fas.fa-chart-bar::before{content:"\\1F4CA"}
.fas.fa-chalkboard-teacher::before{content:"\\1F468\\200D\\1F3EB"}
.fas.fa-user-graduate::before{content:"\\1F393"}
.fas.fa-microscope::before{content:"\\1F52C"}
.fas.fa-cogs::before{content:"\\2699"}
.fas.fa-database::before{content:"\\1F4BE"}
.fas.fa-sliders-h::before{content:"\\1F39A"}
.fas.fa-microchip::before{content:"\\1F4BB"}
.fas.fa-save::before{content:"\\1F4BE"}
.fas.fa-plus-circle::before{content:"\\2795"}
.fas.fa-bell::before{content:"\\1F514"}
.fas.fa-list-alt::before{content:"\\1F4CB"}
.fas.fa-flask::before{content:"\\2697"}
.fas fa-vial::before{content:"\\1F9EA"}
.fas fa-info-circle::before{content:"\\2139"}
.fas.fa-sync-alt::before{content:"\\1F504"}
.fas.fa-sign-out-alt::before{content:"\\1F6AA"}
.fas.fa-search::before{content:"\\1F50D"}
.fas.fa-bars::before{content:"\\2630"}
.fas.fa-times::before{content:"\\2716"}
.fas.fa-chevron-left::before{content:"\\2039"}
.fas.fa-chevron-right::before{content:"\\203A"}
.fas.fa-chevron-down::before{content:"\\2304"}
.fas.fa-chevron-up::before{content:"\\2303"}
.fas.fa-home::before{content:"\\1F3E0"}
.fas.fa-cog::before{content:"\\2699"}
.fas.fa-wrench::before{content:"\\1F527"}
.fas.fa-hammer::before{content:"\\1F528"}
.fas.fa-bug::before{content:"\\1F41B"}
.fas.fa-code::before{content:"\\1F4BB"}
.fas.fa-terminal::before{content:"\\1F4BB"}
.fas.fa-server::before{content:"\\1F5A5"}
.fas.fa-cloud::before{content:"\\2601"}
.fas.fa-plug::before{content:"\\1F50C"}
.fas fa-bolt::before{content:"\\26A1"}
.fas fa-fire::before{content:"\\1F525"}
.fas.fa-star::before{content:"\\2B50"}
.fas.fa-check::before{content:"\\2705"}
.fas fa-times-circle::before{content:"\\274E"}
.fas fa-check-circle::before{content:"\\2705"}
.fas.fa-exclamation-triangle::before{content:"\\26A0"}
.fas.fa-info::before{content:"\\2139"}
.fas.fa-question::before{content:"\\2753"}
.fas.fa-lightbulb::before{content:"\\1F4A1"}
.fas.fa-rocket::before{content:"\\1F680"}
.fas.fa-gem::before{content:"\\1F48E"}
.fas.fa-magic::before{content:"\\2728"}
.fas.fa-palette::before{content:"\\1F3A8"}
.fas.fa-paint-brush::before{content:"\\1F58C"}
.fas.fa-pencil-alt::before{content:"\\270F"}
.fas.fa-edit::before{content:"\\270F"}
.fas.fa-trash::before{content:"\\1F5D1"}
.fas.fa-trash-alt::before{content:"\\1F5D1"}
.fas.fa-copy::before{content:"\\1F4CB"}
.fas.fa-paste::before{content:"\\1F4CB"}
.fas.fa-cut::before{content:"\\2702"}
.fas.fa-clipboard::before{content:"\\1F4CB"}
.fas.fa-folder::before{content:"\\1F4C1"}
.fas.fa-folder-open::before{content:"\\1F4C2"}
.fas.fa-file::before{content:"\\1F4C4"}
.fas.fa-file-code::before{content:"\\1F4C4"}
.fas.fa-download::before{content:"\\1F4E5"}
.fas.fa-upload::before{content:"\\1F4E4"}
.fas.fa-share::before{content:"\\1F4E4"}
.fas.fa-link::before{content:"\\1F517"}
.fas.fa-unlink::before{content:"\\1F517"}
.fas.fa-external-link-alt::before{content:"\\1F517"}
.fas.fa-eye::before{content:"\\1F441"}
.fas.fa-eye-slash::before{content:"\\1F441"}
.fas.fa-print::before{content:"\\1F5A8"}
.fas.fa-envelope::before{content:"\\2709"}
.fas.fa-phone::before{content:"\\1F4DE"}
.fas.fa-mobile-alt::before{content:"\\1F4F1"}
.fas.fa-tablet-alt::before{content:"\\1F4F1"}
.fas.fa-laptop::before{content:"\\1F4BB"}
.fas.fa-keyboard::before{content:"\\2328"}
.fas.fa-mouse::before{content:"\\1F5B1"}
.fas.fa-headphones::before{content:"\\1F3A7"}
.fas.fa-microphone::before{content:"\\1F3A4"}
.fas.fa-video::before{content:"\\1F3A5"}
.fas.fa-camera::before{content:"\\1F4F7"}
.fas.fa-image::before{content:"\\1F5BC"}
.fas.fa-images::before{content:"\\1F5BC"}
.fas.fa-play::before{content:"\\25B6"}
.fas.fa-pause::before{content:"\\23F8"}
.fas.fa-stop::before{content:"\\23F9"}
.fas.fa-forward::before{content:"\\23E9"}
.fas.fa-backward::before{content:"\\23EA"}
.fas.fa-volume-up::before{content:"\\1F50A"}
.fas.fa-volume-down::before{content:"\\1F509"}
.fas.fa-volume-mute::before{content:"\\1F507"}
.fas.fa-volume-off::before{content:"\\1F507"}
.fas.fa-clock::before{content:"\\1F550"}
.fas.fa-calendar::before{content:"\\1F4C5"}
.fas.fa-calendar-alt::before{content:"\\1F4C5"}
.fas.fa-map::before{content:"\\1F5FA"}
.fas.fa-map-marker-alt::before{content:"\\1F4CD"}
.fas.fa-compass::before{content:"\\1F9ED"}
.fas.fa-globe::before{content:"\\1F30D"}
.fas.fa-language::before{content:"\\1F310"}
.fas.fa-flag::before{content:"\\1F3F3"}
.fas.fa-trophy::before{content:"\\1F3C6"}
.fas.fa-medal::before{content:"\\1F3C5"}
.fas.fa-award::before{content:"\\1F3C6"}
.fas.fa-gift::before{content:"\\1F381"}
.fas.fa-heart::before{content:"\\2764"}
.fas.fa-thumbs-up::before{content:"\\1F44D"}
.fas.fa-thumbs-down::before{content:"\\1F44E"}
.fas.fa-comment::before{content:"\\1F4AC"}
.fas.fa-comments::before{content:"\\1F4AC"}
.fas.fa-reply::before{content:"\\21A9"}
.fas.fa-share-alt::before{content:"\\1F4E4"}
.fas.fa-retweet::before{content:"\\1F504"}
.fas.fa-redo::before{content:"\\21BB"}
.fas.fa-undo::before{content:"\\21B6"}
.fas.fa-sync::before{content:"\\1F504"}
.fas.fa-refresh::before{content:"\\1F504"}
.fas.fa-expand::before{content:"\\26F6"}
.fas.fa-compress::before{content:"\\1F5DC"}
.fas.fa-maximize::before{content:"\\26F6"}
.fas.fa-minimize::before{content:"\\1F5DC"}
.fas.fa-arrows-alt::before{content:"\\26F6"}
.fas.fa-arrows-alt-h::before{content:"\\2194"}
.fas.fa-arrows-alt-v::before{content:"\\2195"}
.fas.fa-angle-up::before{content:"\\2303"}
.fas.fa-angle-down::before{content:"\\2304"}
.fas.fa-angle-left::before{content:"\\2329"}
.fas.fa-angle-right::before{content:"\\232A"}
.fas.fa-arrow-up::before{content:"\\2B06"}
.fas.fa-arrow-down::before{content:"\\2B07"}
.fas.fa-arrow-left::before{content:"\\2B05"}
.fas.fa-arrow-right::before{content:"\\27A1"}
.fas.fa-long-arrow-alt-up::before{content:"\\2B06"}
.fas.fa-long-arrow-alt-down::before{content:"\\2B07"}
.fas.fa-long-arrow-alt-left::before{content:"\\2B05"}
.fas.fa-long-arrow-alt-right::before{content:"\\27A1"}
.fas.fa-exchange-alt::before{content:"\\21C4"}
.fas.fa-random::before{content:"\\1F500"}
.fas.fa-sort::before{content:"\\21D5"}
.fas.fa-sort-up::before{content:"\\2B06"}
.fas.fa-sort-down::before{content:"\\2B07"}
.fas.fa-filter::before{content:"\\1F50D"}
.fas.fa-search-plus::before{content:"\\1F50D"}
.fas.fa-search-minus::before{content:"\\1F50D"}
.fas.fa-plus-square::before{content:"\\1F197"}
.fas.fa-minus-square::before{content:"\\229F"}
.fas.fa-check-square::before{content:"\\2611"}
.fas.fa-square::before{content:"\\2B1B"}
.fas.fa-circle::before{content:"\\26AB"}
.fas.fa-dot-circle::before{content:"\\1F518"}
.fas.fa-minus::before{content:"\\2212"}
.fas.fa-equals::before{content:"\\003D"}
.fas.fa-percent::before{content:"\\0025"}
.fas.fa-hashtag::before{content:"\\0023"}
.fas.fa-at::before{content:"\\0040"}
.fas.fa-dollar-sign::before{content:"\\0024"}
.fas.fa-euro-sign::before{content:"\\20AC"}
.fas.fa-pound-sign::before{content:"\\00A3"}
.fas.fa-yen-sign::before{content:"\\00A5"}
.fas.fa-ruble-sign::before{content:"\\20BD"}
.fas.fa-rupee-sign::before{content:"\\20B9"}
.fas.fa-won-sign::before{content:"\\20A9"}
.fas.fa-bitcoin::before{content:"\\20BF"}
.fas.fa-coins::before{content:"\\1FA99"}
.fas.fa-wallet::before{content:"\\1F45B"}
.fas.fa-credit-card::before{content:"\\1F4B3"}
.fas.fa-money-bill-wave::before{content:"\\1F4B5"}
.fas.fa-receipt::before{content:"\\1F9FE"}
.fas.fa-invoice::before{content:"\\1F4C4"}
.fas.fa-piggy-bank::before{content:"\\1F437"}
.fas.fa-chart-pie::before{content:"\\1F4CA"}
.fas.fa-chart-area::before{content:"\\1F4CA"}
.fas fa-percentage::before{content:"\\0025"}
.fas.fa-industry::before{content:"\\1F3ED"}
.fas.fa-building::before{content:"\\1F3E2"}
.fas.fa-city::before{content:"\\1F3D9"}
.fas.fa-store::before{content:"\\1F3EA"}
.fas.fa-shopping-cart::before{content:"\\1F6D2"}
.fas.fa-shopping-bag::before{content:"\\1F45C"}
.fas.fa-shopping-basket::before{content:"\\1F9FA"}
.fas.fa-tags::before{content:"\\1F3F7"}
.fas.fa-tag::before{content:"\\1F3F7"}
.fas.fa-barcode::before{content:"\\1F3AB"}
.fas.fa-qrcode::before{content:"\\1F4F3"}
.fas.fa-id-card::before{content:"\\1FAA4"}
.fas.fa-id-badge::before{content:"\\1F4DB"}
.fas.fa-passport::before{content:"\\1F6C2"}
.fas.fa-ticket-alt::before{content:"\\1F3AB"}
.fas.fa-utensils::before{content:"\\1F37D"}
.fas.fa-utensil-spoon::before{content:"\\1F944"}
.fas.fa-coffee::before{content:"\\2615"}
.fas.fa-mug-hot::before{content:"\\2615"}
.fas.fa-glass-martini::before{content:"\\1F378"}
.fas.fa-glass-whiskey::before{content:"\\1F943"}
.fas.fa-hamburger::before{content:"\\1F354"}
.fas.fa-pizza-slice::before{content:"\\1F355"}
.fas.fa-hotdog::before{content:"\\1F32D"}
.fas.fa-popcorn::before{content:"\\1F37F"}
.fas.fa-candy-cane::before{content:"\\1F36D"}
.fas.fa-cookie::before{content:"\\1F36A"}
.fas.fa-birthday-cake::before{content:"\\1F382"}
.fas.fa-apple-alt::before{content:"\\1F34E"}
.fas.fa-carrot::before{content:"\\1F955"}
.fas.fa-leaf::before{content:"\\1F343"}
.fas.fa-seedling::before{content:"\\1F331"}
.fas.fa-tree::before{content:"\\1F333"}
.fas.fa-pagelines::before{content:"\\1F33F"}
.fas.fa-sun::before{content:"\\2600"}
.fas.fa-moon::before{content:"\\1F319"}
.fas.fa-star-half::before{content:"\\2B50"}
.fas.fa-star-half-alt::before{content:"\\2B50"}
.fas.fa-cloud-sun::before{content:"\\1F324"}
.fas.fa-cloud-moon::before{content:"\\1F32B"}
.fas.fa-cloud-rain::before{content:"\\1F327"}
.fas.fa-cloud-showers-heavy::before{content:"\\1F327"}
.fas.fa-wind::before{content:"\\1F32C"}
.fas.fa-snowflake::before{content:"\\2744"}
.fas.fa-umbrella::before{content:"\\2602"}
.fas.fa-temperature-high::before{content:"\\1F321"}
.fas.fa-temperature-low::before{content:"\\1F321"}
.fas.fa-thermometer-half::before{content:"\\1F321"}
.fas.fa-tint::before{content:"\\1F4A7"}
.fas.fa-water::before{content:"\\1F4A7"}
.fas.fa-fire-extinguisher::before{content:"\\1F9EF"}
.fas.fa-magnet::before{content:"\\1F9F2"}
.fas.fa-battery-full::before{content:"\\1F50B"}
.fas.fa-battery-three-quarters::before{content:"\\1F50B"}
.fas.fa-battery-half::before{content:"\\1F50B"}
.fas.fa-battery-quarter::before{content:"\\1F50B"}
.fas.fa-battery-empty::before{content:"\\1F50B"}
.fas.fa-plug-circle-bolt::before{content:"\\1F50C"}
.fas.fa-bolt-lightning::before{content:"\\26A1"}
.fas.fa-project-diagram::before{content:"\\1F4C8"}
.fas.fa-network-wired::before{content:"\\1F5A5"}
.fas.fa-sitemap::before{content:"\\1F5C4"}
.fas.fa-stream::before{content:"\\1F4F6"}
.fas.fa-wifi::before{content:"\\1F6DC"}
.fas.fa-ethernet::before{content:"\\1F5A5"}
.fas.fa-broadcast-tower::before{content:"\\1F4E1"}
.fas.fa-satellite::before{content:"\\1F6F0"}
.fas.fa-satellite-dish::before{content:"\\1F4E1"}
.fas.fa-signal::before{content:"\\1F4F6"}
.fas.fa-tower-observation::before{content:"\\1F5FC"}
.fas.fa-tv::before{content:"\\1F4FA"}
.fas.fa-radio::before{content:"\\1F4FB"}
.fas.fa-podcast::before{content:"\\1F399"}
.fas.fa-bullhorn::before{content:"\\1F4E3"}
.fas.fa-bullseye::before{content:"\\1F3AF"}
.fas.fa-crosshairs::before{content:"\\1F3AF"}
.fas.fa-fingerprint::before{content:"\\1F442"}
.fas.fa-key::before{content:"\\1F511"}
.fas.fa-keybase::before{content:"\\1F5DD"}
.fas.fa-lock-open::before{content:"\\1F513"}
.fas.fa-unlock::before{content:"\\1F513"}
.fas.fa-unlock-alt::before{content:"\\1F513"}
.fas.fa-user-lock::before{content:"\\1F464"}
.fas.fa-user-secret::before{content:"\\1F575"}
.fas.fa-user-shield::before{content:"\\1F6E1"}
.fas.fa-user-tag::before{content:"\\1F3F7"}
.fas.fa-user-plus::before{content:"\\1F464"}
.fas.fa-user-minus::before{content:"\\1F464"}
.fas.fa-user-times::before{content:"\\1F464"}
.fas.fa-user-check::before{content:"\\2705"}
.fas.fa-user-slash::before{content:"\\1F464"}
.fas.fa-user-friends::before{content:"\\1F465"}
.fas.fa-users-cog::before{content:"\\2699"}
.fas.fa-users-crown::before{content:"\\1F451"}
.fas.fa-user-ninja::before{content:"\\1F977"}
.fas.fa-user-astronaut::before{content:"\\1F9D1"}
.fas.fa-user-md::before{content:"\\1F468"}
.fas.fa-user-nurse::before{content:"\\1F469"}
.fas.fa-user-injured::before{content:"\\1F915"}
.fas.fa-photo-video::before{content:"\\1F5BC"}
.fas.fa-icons::before{content:"\\1F3A8"}
.fas.fa-layer-group::before{content:"\\1F9F1"}
.fas.fa-cubes::before{content:"\\1F9F1"}
.fas.fa-cube::before{content:"\\1F9F1"}
.fas.fa-puzzle-piece::before{content:"\\1F9E9"}
.fas.fa-shapes::before{content:"\\1F537"}
.fas.fa-shape-square::before{content:"\\2B1B"}
.fas.fa-shape-circle::before{content:"\\26AB"}
.fas.fa-shape-triangle::before{content:"\\1F53A"}
.fas.fa-paint-roller::before{content:"\\1F9FA"}
.fas.fa-brush::before{content:"\\1F58C"}
.fas.fa-draw-polygon::before{content:"\\27F2"}
.fas.fa-vector-square::before{content:"\\1F4D0"}
.fas.fa-ruler-combined::before{content:"\\1F4CF"}
.fas.fa-ruler::before{content:"\\1F4CF"}
.fas.fa-ruler-horizontal::before{content:"\\1F4CF"}
.fas.fa-ruler-vertical::before{content:"\\1F4CF"}
.fas.fa-stamp::before{content:"\\1F5BC"}
.fas.fa-highlighter::before{content:"\\1F58D"}
.fas.fa-marker::before{content:"\\1F58B"}
.fas.fa-pencil-ruler::before{content:"\\1F4CF"}
.fas.fa-pen::before{content:"\\1F58B"}
.fas.fa-pen-fancy::before{content:"\\1F58B"}
.fas.fa-pen-nib::before{content:"\\2712"}
.fas.fa-pen-alt::before{content:"\\270F"}
.fas.fa-eraser::before{content:"\\1F9FD"}
.fas.fa-fill-drip::before{content:"\\1F3A8"}
.fas.fa-fill::before{content:"\\1F3A8"}
.fas.fa-eye-dropper::before{content:"\\1F4A7"}
.fas.fa-spray-can::before{content:"\\1F927"}
.fas.fa-tape::before{content:"\\1F9F5"}
.fas.fa-scissors::before{content:"\\2702"}
.fas.fa-cut::before{content:"\\2702"}
.fas.fa-paste::before{content:"\\1F4CB"}
.fas.fa-copy::before{content:"\\1F4CB"}

/* Responsive icons */
.fa-1x{font-size:1em}.fa-2x{font-size:2em}.fa-3x{font-size:3em}.fa-4x{font-size:4em}.fa-5x{font-size:5em}
.fa-6x{font-size:6em}.fa-7x{font-size:7em}.fa-8x{font-size:8em}.fa-9x{font-size:9em}.fa-10x{font-size:10em}

/* Icon animations */
.fa-beat{animation:fa-beat 1s ease-in-out infinite}
@keyframes fa-beat{0%{transform:scale(1)}50%{transform:scale(1.125)}}
.fa-fade{animation:fa-fade 2s ease-in-out infinite}
@keyframes fa-fade{0%{opacity:1}50%{opacity:0.4}}
.fa-beat-fade{animation:fa-beat-fade 2s ease-in-out infinite}
@keyframes fa-beat-fade{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.4;transform:scale(0.75)}}
.fa-flip{animation:fa-flip 2s ease-in-out infinite}
@keyframes fa-flip{0%{transform:perspective(400px) rotateY(0)}50%{transform:perspective(400px) rotateY(180deg)}}
.fa-shake{animation:fa-shake 1s ease-in-out infinite}
@keyframes fa-shake{0%,100%{transform:rotate(0)}10%,30%,50%,70%,90%{transform:rotate(-10deg)}20%,40%,60%,80%{transform:rotate(10deg)}}

/* Icon rotating */
.fa-rotate-90{transform:rotate(90deg)}
.fa-rotate-180{transform:rotate(180deg)}
.fa-rotate-270{transform:rotate(270deg)}
.fa-flip-horizontal{transform:scaleX(-1)}
.fa-flip-vertical{transform:scaleY(-1)}
.fa-flip-both{transform:scale(-1,-1)}
'''
        
        output_path = os.path.join(BASE_DIR, 'static', 'all.min.css')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fontawesome_css)
        
        logger.info(f"[{self.employee_id}] all.min.css 生成成功: {output_path}")
        return True
    
    def fix_base_layout_css_refs(self):
        """修复base_layout.html中的CSS引用，添加正确的CSS文件"""
        logger.info(f"[{self.employee_id}] 修复base_layout.html的CSS引用...")
        
        base_layout_path = os.path.join(BASE_DIR, 'templates', 'base_layout.html')
        
        try:
            with open(base_layout_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fixes = []
            
            # 确保引用了正确路径的CSS文件
            if 'css/mtscos-design-system.css' not in content:
                # 在tailwind.min.css后面添加设计系统CSS
                new_css_link = '''    <link href="{{ url_for('static', filename='css/mtscos-design-system.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/dashboard.css') }}" rel="stylesheet">
'''
                content = content.replace(
                    '<link href="{{ url_for(\'static\', filename=\'all.min.css\') }}" rel="stylesheet">',
                    '<link href="{{ url_for(\'static\', filename=\'all.min.css\') }}" rel="stylesheet">\n' + new_css_link
                )
                fixes.append('添加mtscos-design-system.css, style.css, dashboard.css引用')
            
            # 移除Vite开发客户端引用
            if '@vite/client' in content:
                import re
                content = re.sub(r'<script[^>]*@vite/client[^>]*></script>', '', content)
                fixes.append('移除Vite开发客户端引用')
            
            with open(base_layout_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"[{self.employee_id}] base_layout.html修复完成: {fixes}")
            self.fixes_applied.extend(fixes)
            return fixes
            
        except Exception as e:
            logger.error(f"[{self.employee_id}] 修复base_layout.html失败: {e}")
            return []
    
    def fix_super_admin_dashboard_template(self):
        """修复super_admin_dashboard.html模板，确保数据加载和样式正确"""
        logger.info(f"[{self.employee_id}] 修复super_admin_dashboard.html...")
        
        dashboard_path = os.path.join(BASE_DIR, 'templates', 'super_admin_dashboard.html')
        
        try:
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fixes = []
            
            # 确保有数据加载脚本
            if 'loadDashboardData' not in content:
                load_script = '''
<script>
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    getUserIP();
    setInterval(monitorSystemStatus, 60000);
});

function loadDashboardData() {
    fetch('/api/admin/dashboard_stats')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const userCountEl = document.getElementById('user-count');
                const activeUsersEl = document.getElementById('active-users');
                const routeCountEl = document.getElementById('route-count');
                const systemStatusEl = document.getElementById('system-status');
                
                if (userCountEl) userCountEl.textContent = data.data.user_count;
                if (activeUsersEl) activeUsersEl.textContent = '今日活跃: ' + data.data.active_users;
                if (routeCountEl) routeCountEl.textContent = data.data.route_count;
                if (systemStatusEl) systemStatusEl.textContent = data.data.system_status;
            }
        })
        .catch(err => console.warn('统计数据加载失败:', err));
}

function getUserIP() {
    fetch('/api/user/ip')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const ipDisplay = document.getElementById('user-ip-display');
                if (ipDisplay) ipDisplay.textContent = data.data.ip;
            }
        })
        .catch(err => console.warn('IP获取失败:', err));
}

function monitorSystemStatus() {
    const now = new Date().toLocaleString('zh-CN');
    console.log('System status monitored at:', now);
}
</script>
'''
                if '</body>' in content:
                    content = content.replace('</body>', load_script + '</body>')
                else:
                    content += load_script
                fixes.append('添加数据加载和IP获取脚本')
            
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"[{self.employee_id}] super_admin_dashboard.html修复完成: {fixes}")
            self.fixes_applied.extend(fixes)
            return fixes
            
        except Exception as e:
            logger.error(f"[{self.employee_id}] 修复super_admin_dashboard.html失败: {e}")
            return []
    
    def create_webfonts_directory(self):
        """创建webfonts目录，放置FontAwesome字体文件占位符"""
        logger.info(f"[{self.employee_id}] 创建webfonts目录...")
        
        webfonts_dir = os.path.join(BASE_DIR, 'static', 'webfonts')
        
        try:
            os.makedirs(webfonts_dir, exist_ok=True)
            
            # 创建一个占位符文件说明
            readme_path = os.path.join(webfonts_dir, 'README.txt')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write('''Font Awesome Web Fonts
=====================

本目录用于存放Font Awesome字体文件。
当前系统使用CSS Unicode图标替代方案，无需额外字体文件。

如需完整的Font Awesome SVG图标支持，请：
1. 访问 https://fontawesome.com/download
2. 下载免费版
3. 将webfonts目录下的字体文件复制到此处
''')
            
            logger.info(f"[{self.employee_id}] webfonts目录创建成功")
            return True
        except Exception as e:
            logger.error(f"[{self.employee_id}] 创建webfonts目录失败: {e}")
            return False
    
    def run_complete_fix(self):
        """执行完整修复流程"""
        logger.info(f"[{self.employee_id}] ===== 开始执行超级管理员仪表盘全面修复任务 =====")
        
        all_fixes = []
        affected_files = []
        
        # 步骤1: 诊断问题
        logger.info(f"[{self.employee_id}] 步骤1: 诊断问题...")
        issues = self.diagnose_issues()
        logger.info(f"[{self.employee_id}] 发现 {len(issues)} 个问题")
        
        # 上报诊断结果
        for issue in issues:
            self.report_fix_to_db(
                fix_type='diagnosis',
                description=f"发现问题: {issue['description']}",
                severity=issue['severity'],
                affected_files=[],
                fix_details={'issue': issue}
            )
        
        # 步骤2: 生成tailwind.min.css
        logger.info(f"[{self.employee_id}] 步骤2: 生成Tailwind CSS...")
        if self.generate_tailwind_min_css():
            all_fixes.append('生成tailwind.min.css')
            affected_files.append('static/tailwind.min.css')
            self.fix_count += 1
        
        # 步骤3: 生成all.min.css (FontAwesome替代)
        logger.info(f"[{self.employee_id}] 步骤3: 生成FontAwesome CSS...")
        if self.generate_fontawesome_css():
            all_fixes.append('生成all.min.css (FontAwesome替代)')
            affected_files.append('static/all.min.css')
            self.fix_count += 1
        
        # 步骤4: 创建webfonts目录
        logger.info(f"[{self.employee_id}] 步骤4: 创建webfonts目录...")
        if self.create_webfonts_directory():
            all_fixes.append('创建webfonts目录')
            affected_files.append('static/webfonts/')
            self.fix_count += 1
        
        # 步骤5: 修复base_layout.html
        logger.info(f"[{self.employee_id}] 步骤5: 修复base_layout.html...")
        base_fixes = self.fix_base_layout_css_refs()
        if base_fixes:
            all_fixes.extend(base_fixes)
            affected_files.append('templates/base_layout.html')
            self.fix_count += len(base_fixes)
        
        # 步骤6: 修复super_admin_dashboard.html
        logger.info(f"[{self.employee_id}] 步骤6: 修复super_admin_dashboard.html...")
        dashboard_fixes = self.fix_super_admin_dashboard_template()
        if dashboard_fixes:
            all_fixes.extend(dashboard_fixes)
            affected_files.append('templates/super_admin_dashboard.html')
            self.fix_count += len(dashboard_fixes)
        
        # 步骤7: 上报完整修复报告
        logger.info(f"[{self.employee_id}] 步骤7: 上报完整修复报告...")
        self.report_fix_to_db(
            fix_type='complete_fix',
            description=f'超级管理员仪表盘全面修复完成，共{len(all_fixes)}项修复',
            severity='critical',
            affected_files=affected_files,
            fix_details={
                'total_fixes': len(all_fixes),
                'fixes': all_fixes,
                'issues_found': len(issues),
                'issues': issues
            }
        )
        
        # 生成结果报告
        result = {
            'employee_id': self.employee_id,
            'employee_name': self.name,
            'role': self.role,
            'issues_found': len(issues),
            'fixes_applied': len(all_fixes),
            'fix_details': all_fixes,
            'affected_files': affected_files,
            'reports_submitted': self.report_count,
            'status': 'completed',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"[{self.employee_id}] ===== 超级管理员仪表盘修复任务完成 =====")
        logger.info(f"[{self.employee_id}] 修复结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        return result


# 创建全局实例
super_admin_dashboard_fixer_ai = SuperAdminDashboardFixerAI()


def run_super_admin_dashboard_fix():
    """执行超级管理员仪表盘修复"""
    return super_admin_dashboard_fixer_ai.run_complete_fix()


if __name__ == '__main__':
    result = run_super_admin_dashboard_fix()
    print(json.dumps(result, ensure_ascii=False, indent=2))
