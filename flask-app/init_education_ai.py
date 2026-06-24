#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动初始化教育和考试系统 AI 员工
根据用户教育类型自动创建对应的专业 AI 员工
"""

import sqlite3
import json
import uuid
import os
from datetime import datetime

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def init_education_ai_employees():
    """初始化教育类型相关的 AI 员工"""
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 检查 ai_employees 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_employees'")
        if not cursor.fetchone():
            print("❌ ai_employees 表不存在，跳过 AI 员工初始化")
            return
        
        # 定义需要创建的 AI 员工
        ai_employees = [
            {
                'code': 'EDU_NINE_YEAR',
                'name': '九年制义务教育辅导员',
                'description': '专注于九年制义务教育阶段的学习辅导、考试指导、课程推荐',
                'specialties': 'nine_year_education',
                'grade_levels': ['小学1-6年级', '初中1-3年级', '高中1-3年级'],
                'capabilities': [
                    '学科知识辅导', '考试技巧指导', '学习计划制定',
                    '知识点讲解', '习题解答', '学习进度跟踪'
                ],
                'status': 'active'
            },
            {
                'code': 'EDU_ADULT',
                'name': '成人教育顾问',
                'description': '专注于成人继续教育、职业技能提升、语言学习等教育服务',
                'specialties': 'adult_education',
                'grade_levels': ['成人大学', '成人日语N5-N1', '成人英语'],
                'capabilities': [
                    '成人学习规划', '职业技能培训', '语言学习辅导',
                    '学历提升指导', '职业资格培训', '学习时间管理'
                ],
                'status': 'active'
            },
            {
                'code': 'EXAM_NINE_YEAR',
                'name': '九年制考试专家',
                'description': '专注于九年制义务教育阶段的各类考试，包括月考、期中考、期末考、中考等',
                'specialties': 'nine_year_exam',
                'exam_types': ['月考', '期中考试', '期末考试', '中考模拟', '学业水平测试'],
                'capabilities': [
                    '考试命题分析', '考点归纳总结', '答题技巧训练',
                    '模拟试题生成', '考试成绩分析', '错题本管理'
                ],
                'status': 'active'
            },
            {
                'code': 'EXAM_ADULT',
                'name': '成人教育考试专家',
                'description': '专注于成人教育的各类考试，包括成人高考、学位英语、日语等级考试等',
                'specialties': 'adult_exam',
                'exam_types': ['成人高考', '学位英语', '日语能力考N5-N1', '英语等级考试'],
                'capabilities': [
                    '考试政策解读', '备考计划制定', '重点难点突破',
                    '真题解析', '应试技巧培训', '考前冲刺辅导'
                ],
                'status': 'active'
            }
        ]
        
        created_count = 0
        for emp in ai_employees:
            # 检查是否已存在
            cursor.execute('SELECT id FROM ai_employees WHERE employee_code = ?', (emp['code'],))
            existing = cursor.fetchone()
            
            if existing:
                print(f"✓ {emp['name']} (代码: {emp['code']}) 已存在，跳过")
                continue
            
            # 创建新员工
            now = datetime.now().isoformat()
            
            capabilities_json = json.dumps(emp['capabilities'], ensure_ascii=False)
            
            cursor.execute('''
                INSERT INTO ai_employees (
                    employee_code, name, description, specialties,
                    capabilities, status, created_at, updated_at, accuracy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp['code'],
                emp['name'],
                emp['description'],
                emp['specialties'],
                capabilities_json,
                emp['status'],
                now,
                now,
                0.95  # accuracy
            ))
            
            created_count += 1
            print(f"✅ 创建 AI 员工: {emp['name']} (代码: {emp['code']})")
        
        # 创建教育类型权限规则
        rules = [
            {
                'rule_code': 'PERM_NINE_YEAR_EDUCATION',
                'rule_value': '["student"]',
                'description': '九年制义务教育权限'
            },
            {
                'rule_code': 'PERM_ADULT_EDUCATION',
                'rule_value': '["student"]',
                'description': '成人教育权限'
            },
            {
                'rule_code': 'PERM_NINE_YEAR_EXAM',
                'rule_value': '["student"]',
                'description': '九年制考试权限'
            },
            {
                'rule_code': 'PERM_ADULT_EXAM',
                'rule_value': '["student"]',
                'description': '成人考试权限'
            }
        ]
        
        # 检查并创建规则
        for rule in rules:
            cursor.execute('SELECT rule_code FROM system_rules WHERE rule_code = ?', (rule['rule_code'],))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO system_rules (rule_code, rule_name, rule_description, rule_type, rule_value, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule['rule_code'],
                    rule['rule_code'],
                    rule['description'],
                    'permission',
                    rule['rule_value'],
                    now,
                    now
                ))
                print(f"✅ 创建权限规则: {rule['rule_code']}")
        
        conn.commit()
        
        print(f"\n📊 教育 AI 员工初始化完成！创建了 {created_count} 个新员工")

def bind_education_routes():
    """绑定教育类型相关的路由权限"""
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 教育类型路由配置
        education_routes = [
            {
                'route': '/exam/major_placement_test',
                'name': '九年制义务教育摸底测试',
                'education_type': 'nine_year',
                'required_permission': 'PERM_NINE_YEAR_EDUCATION'
            },
            {
                'route': '/exam/adult_placement_test',
                'name': '成人教育摸底测试',
                'education_type': 'adult',
                'required_permission': 'PERM_ADULT_EDUCATION'
            },
            {
                'route': '/exam/placement_test',
                'name': '通用摸底测试',
                'education_type': 'general',
                'required_permission': 'PERM_NINE_YEAR_EXAM'
            }
        ]
        
        # 创建路由权限表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS education_route_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route TEXT UNIQUE NOT NULL,
                route_name TEXT,
                education_type TEXT,
                required_permission TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        for route in education_routes:
            cursor.execute('''
                INSERT OR REPLACE INTO education_route_permissions 
                (route, route_name, education_type, required_permission)
                VALUES (?, ?, ?, ?)
            ''', (
                route['route'],
                route['name'],
                route['education_type'],
                route['required_permission']
            ))
            print(f"✅ 绑定路由权限: {route['route']} -> {route['required_permission']}")
        
        conn.commit()
        print(f"\n📊 教育路由权限绑定完成！绑定了 {len(education_routes)} 条路由")

if __name__ == '__main__':
    print("=" * 60)
    print("🎓 开始初始化教育和考试系统 AI 员工")
    print("=" * 60)
    
    try:
        init_education_ai_employees()
        print()
        bind_education_routes()
        print()
        print("✅ 所有初始化任务完成！")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
