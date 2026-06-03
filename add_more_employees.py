#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多AI员工并扩展系统功能
"""

import sqlite3
import json
from datetime import datetime

def add_employee(db_path, name, role, department, avatar, capabilities, score):
    """添加单个AI员工"""
    capabilities_json = json.dumps(capabilities, ensure_ascii=False)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM ai_employees WHERE name = ?', (name,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"⚠️ AI员工 '{name}' 已存在，跳过")
        return None
    
    cursor.execute('''
        INSERT INTO ai_employees 
        (name, role, department, avatar, capabilities, performance_score, tasks_completed)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    ''', (name, role, department, avatar, capabilities_json, score))
    
    employee_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ AI员工 '{name}' 创建成功！ID: {employee_id}")
    return employee_id

def add_more_employees(db_path='mtcos_system.db'):
    """添加更多AI员工"""
    print("=" * 80)
    print("🚀 添加更多AI员工")
    print("=" * 80)
    
    new_employees = [
        {
            'name': '物理大师',
            'role': '物理教学专家',
            'department': '理科学院',
            'avatar': '⚛️',
            'capabilities': ['物理教学', '实验指导', '公式讲解', '竞赛培训'],
            'score': 95.8
        },
        {
            'name': '化学博士',
            'role': '化学教学专家',
            'department': '理科学院',
            'avatar': '🧪',
            'capabilities': ['化学教学', '实验指导', '分子模型', '化学计算'],
            'score': 94.9
        },
        {
            'name': '生物专家',
            'role': '生物教学专家',
            'department': '理科学院',
            'avatar': '🔬',
            'capabilities': ['生物教学', '进化论', '基因工程', '生态系统'],
            'score': 93.7
        },
        {
            'name': '历史老师',
            'role': '历史教学专家',
            'department': '人文学院',
            'avatar': '🏛️',
            'capabilities': ['历史教学', '事件分析', '时间线', '文化讲解'],
            'score': 92.5
        },
        {
            'name': '地理学者',
            'role': '地理教学专家',
            'department': '人文学院',
            'avatar': '🗺️',
            'capabilities': ['地理教学', '地图解析', '气候分析', '人文地理'],
            'score': 91.8
        },
        {
            'name': '政治导师',
            'role': '政治教学专家',
            'department': '人文学院',
            'avatar': '🏛️',
            'capabilities': ['政治教学', '时政分析', '哲学思想', '政策解读'],
            'score': 90.6
        },
        {
            'name': '艺术总监',
            'role': '艺术教学专家',
            'department': '艺术学院',
            'avatar': '🎭',
            'capabilities': ['美术教学', '音乐欣赏', '艺术史', '创作指导'],
            'score': 89.5
        },
        {
            'name': '体育教练',
            'role': '体育健康专家',
            'department': '体育学院',
            'avatar': '🏃',
            'capabilities': ['体育教学', '健康指导', '运动计划', '体能训练'],
            'score': 88.9
        },
        {
            'name': '心理顾问',
            'role': '心理健康专家',
            'department': '心理学院',
            'avatar': '💭',
            'capabilities': ['心理咨询', '压力管理', '情绪调节', '学习心理'],
            'score': 94.2
        },
        {
            'name': '职业规划师',
            'role': '职业发展顾问',
            'department': '就业中心',
            'avatar': '🎯',
            'capabilities': ['职业规划', '简历指导', '面试技巧', '行业分析'],
            'score': 93.1
        },
        {
            'name': '云计算专家',
            'role': '云计算教学专家',
            'department': '计算机学院',
            'avatar': '☁️',
            'capabilities': ['云计算', 'AWS/Azure', 'Docker', 'Kubernetes'],
            'score': 95.5
        },
        {
            'name': 'AI研究员',
            'role': '人工智能研究专家',
            'department': 'AI研究中心',
            'avatar': '🧠',
            'capabilities': ['机器学习', '深度学习', 'NLP', '计算机视觉'],
            'score': 97.2
        }
    ]
    
    added_count = 0
    for emp in new_employees:
        emp_id = add_employee(
            db_path,
            emp['name'],
            emp['role'],
            emp['department'],
            emp['avatar'],
            emp['capabilities'],
            emp['score']
        )
        if emp_id:
            added_count += 1
    
    print(f"\n🎉 成功添加 {added_count} 名新AI员工！")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM ai_employees')
    total = cursor.fetchone()[0]
    conn.close()
    
    print(f"📊 当前AI员工总数: {total} 名")
    return added_count

def create_department_summary(db_path='mtcos_system.db'):
    """创建部门统计信息"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT department, COUNT(*) FROM ai_employees GROUP BY department')
    departments = cursor.fetchall()
    
    print("\n" + "=" * 80)
    print("🏢 部门AI员工统计")
    print("=" * 80)
    
    for dept, count in departments:
        print(f"  • {dept if dept else '未分配'}: {count} 名AI员工")
    
    conn.close()

if __name__ == '__main__':
    add_more_employees()
    create_department_summary()
    print("\n" + "=" * 80)
    print("✅ AI员工扩展完成！")
    print("=" * 80)
