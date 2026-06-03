#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI 员工管理与系统扩展工具
功能：创建、管理、删除AI员工，扩展系统功能
"""

import sqlite3
import json
import random
from datetime import datetime
from pathlib import Path


class AIEmployeeManager:
    """AI员工管理器"""
    
    def __init__(self, db_path='mtcos_system.db'):
        self.db_path = db_path
        self.ensure_database()
    
    def ensure_database(self):
        """确保数据库和表存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT,
                avatar TEXT DEFAULT '🤖',
                capabilities TEXT DEFAULT '[]',
                status TEXT DEFAULT 'active',
                performance_score REAL DEFAULT 85.0,
                tasks_completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                task_type TEXT,
                task_description TEXT,
                status TEXT DEFAULT 'completed',
                completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES ai_employees(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                version TEXT DEFAULT '1.0',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_all_employees(self):
        """获取所有AI员工"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ai_employees ORDER BY performance_score DESC')
        employees = cursor.fetchall()
        conn.close()
        return employees
    
    def add_employee(self, name, role, department=None, avatar='🤖', 
                    capabilities=None, performance_score=85.0):
        """添加新的AI员工"""
        if capabilities is None:
            capabilities = []
        
        capabilities_json = json.dumps(capabilities, ensure_ascii=False)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_employees 
            (name, role, department, avatar, capabilities, performance_score, tasks_completed)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (name, role, department, avatar, capabilities_json, performance_score))
        
        employee_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ AI员工 '{name}' 创建成功！ID: {employee_id}")
        return employee_id
    
    def delete_employee(self, employee_id):
        """删除AI员工"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM ai_employees WHERE id = ?', (employee_id,))
        employee = cursor.fetchone()
        
        if employee:
            cursor.execute('DELETE FROM ai_employees WHERE id = ?', (employee_id,))
            cursor.execute('DELETE FROM ai_task_history WHERE employee_id = ?', (employee_id,))
            conn.commit()
            print(f"🗑️  AI员工 '{employee[0]}' 已删除！")
        
        conn.close()
    
    def display_employees(self):
        """显示所有AI员工"""
        employees = self.get_all_employees()
        
        print("\n" + "=" * 80)
        print("🤖 MTSCOS AI 员工列表")
        print("=" * 80)
        
        if not employees:
            print("📭 暂无AI员工")
        else:
            for emp in employees:
                try:
                    capabilities = json.loads(emp[5])
                except:
                    capabilities = []
                
                print(f"\n📋 ID: {emp[0]}")
                print(f"👤 姓名: {emp[1]}")
                print(f"💼 角色: {emp[2]}")
                print(f"🏢 部门: {emp[3] if emp[3] else '未分配'}")
                print(f"🎭 头像: {emp[4]}")
                print(f"⚡ 能力: {', '.join(capabilities) if capabilities else '无'}")
                print(f"📊 评分: {emp[7]}")
                print(f"✅ 任务: {emp[8]}")
                print(f"📅 创建: {emp[9]}")
                print("-" * 60)
        
        print(f"\n📊 总计: {len(employees)} 名AI员工")
    
    def create_default_employees(self):
        """创建默认的AI员工团队"""
        employees_data = [
            {
                'name': '小智',
                'role': '考试监督员',
                'department': '考试中心',
                'avatar': '👨‍🏫',
                'capabilities': ['考试监控', '成绩分析', '题目推荐'],
                'score': 92.5
            },
            {
                'name': '小雅',
                'role': '日语教学助手',
                'department': '日语学院',
                'avatar': '🗾',
                'capabilities': ['日语教学', 'JLPT培训', '翻译服务'],
                'score': 91.8
            },
            {
                'name': '小能',
                'role': '算法导师',
                'department': '计算机学院',
                'avatar': '💻',
                'capabilities': ['算法指导', '代码评审', '编程训练'],
                'score': 94.2
            },
            {
                'name': '小蓝',
                'role': 'AI学习教练',
                'department': '学习中心',
                'avatar': '🤖',
                'capabilities': ['AI教学', '自适应学习', '进度追踪'],
                'score': 96.1
            },
            {
                'name': '小美',
                'role': 'UI设计师',
                'department': '设计中心',
                'avatar': '🎨',
                'capabilities': ['UI设计', '颜色搭配', '响应式布局'],
                'score': 90.5
            },
            {
                'name': '小安',
                'role': '安全专家',
                'department': '安全中心',
                'avatar': '🛡️',
                'capabilities': ['安全审计', '漏洞检测', '防护策略'],
                'score': 95.3
            },
            {
                'name': '小博',
                'role': '数据分析员',
                'department': '数据中心',
                'avatar': '📊',
                'capabilities': ['数据分析', '图表生成', '报告撰写'],
                'score': 88.7
            },
            {
                'name': '小教',
                'role': '中文教学助手',
                'department': '语言学院',
                'avatar': '📚',
                'capabilities': ['中文教学', '写作指导', '文化讲解'],
                'score': 89.4
            },
            {
                'name': '小音',
                'role': '听力训练师',
                'department': '语言学院',
                'avatar': '🎧',
                'capabilities': ['听力训练', '发音纠正', '口语练习'],
                'score': 87.6
            },
            {
                'name': '小程',
                'role': '编程教练',
                'department': '计算机学院',
                'avatar': '⚙️',
                'capabilities': ['编程教学', '代码调试', '项目指导'],
                'score': 93.8
            }
        ]
        
        print("🚀 创建默认AI员工团队...")
        for emp_data in employees_data:
            self.add_employee(
                emp_data['name'],
                emp_data['role'],
                emp_data['department'],
                emp_data['avatar'],
                emp_data['capabilities'],
                emp_data['score']
            )
        
        print(f"\n🎉 成功创建 {len(employees_data)} 名AI员工！")


class SystemModuleManager:
    """系统模块管理器"""
    
    def __init__(self, db_path='mtcos_system.db'):
        self.db_path = db_path
    
    def add_module(self, name, description, version='1.0'):
        """添加系统模块"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_modules (name, description, version)
            VALUES (?, ?, ?)
        ''', (name, description, version))
        
        module_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ 模块 '{name}' 添加成功！")
        return module_id
    
    def create_default_modules(self):
        """创建默认系统模块"""
        modules = [
            {
                'name': '考试管理系统',
                'description': '考试管理、成绩记录、题目管理',
                'version': '3.3.0'
            },
            {
                'name': 'AI员工系统',
                'description': 'AI员工管理、任务分配、绩效追踪',
                'version': '3.3.0'
            },
            {
                'name': '学习中心',
                'description': '自适应学习、课程管理、进度追踪',
                'version': '3.3.0'
            },
            {
                'name': '用户管理',
                'description': '用户认证、权限管理、个人设置',
                'version': '3.3.0'
            },
            {
                'name': '数据分析',
                'description': '数据可视化、报告生成、统计分析',
                'version': '3.3.0'
            },
            {
                'name': '安全系统',
                'description': '安全审计、防护策略、日志监控',
                'version': '3.3.0'
            }
        ]
        
        print("\n🏗️ 创建系统模块...")
        for module in modules:
            self.add_module(module['name'], module['description'], module['version'])
        
        print(f"✅ 成功创建 {len(modules)} 个系统模块！")


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 MTSCOS AI 员工管理与系统扩展工具")
    print("=" * 80)
    
    emp_manager = AIEmployeeManager()
    mod_manager = SystemModuleManager()
    
    existing_employees = emp_manager.get_all_employees()
    
    if not existing_employees:
        print("\n📥 检测到数据库为空，正在创建默认AI员工团队...")
        emp_manager.create_default_employees()
        mod_manager.create_default_modules()
    else:
        print(f"\n✅ 数据库中已有 {len(existing_employees)} 名AI员工")
        emp_manager.display_employees()
    
    print("\n" + "=" * 80)
    print("💡 功能说明:")
    print("-" * 80)
    print("  • 运行此脚本自动初始化AI员工系统")
    print("  • AI员工数据存储在 mtcos_system.db")
    print("  • 通过API端点可以管理AI员工")
    print("=" * 80)


if __name__ == '__main__':
    main()
