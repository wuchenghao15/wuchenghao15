# -*- coding: utf-8 -*-
"""
测试用户生成脚本
为MTSCOS系统的每个角色创建测试用户，供开发者和测试人员使用
"""

import sqlite3
import hashlib
import os
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                       'split_databases/auth.db')

TEST_PASSWORD = 'Test@2026'

ROLES = [
    {'role': 'student', 'username': 'test_student', 'email': 'student@mtscos.test', 
     'name': '测试学生', 'grade': '高一', 'student_type': 'k12', 'education_level': '高中'},
    {'role': 'parent', 'username': 'test_parent', 'email': 'parent@mtscos.test', 
     'name': '测试家长', 'occupation': '工程师', 'age': 40},
    {'role': 'designer', 'username': 'test_designer', 'email': 'designer@mtscos.test', 
     'name': '测试设计师', 'occupation': '设计师', 'age': 30},
    {'role': 'teacher', 'username': 'test_teacher', 'email': 'teacher@mtscos.test', 
     'name': '测试教师', 'occupation': '教师', 'age': 35},
    {'role': 'exam_proctor', 'username': 'test_proctor', 'email': 'proctor@mtscos.test', 
     'name': '测试监考员', 'occupation': '监考员', 'age': 32},
    {'role': 'question_manager', 'username': 'test_qm', 'email': 'qm@mtscos.test', 
     'name': '测试题库管理员', 'occupation': '题库管理员', 'age': 28},
    {'role': 'ai_manager', 'username': 'test_aim', 'email': 'aim@mtscos.test', 
     'name': '测试AI管理员', 'occupation': 'AI工程师', 'age': 29},
    {'role': 'cluster_manager', 'username': 'test_cm', 'email': 'cm@mtscos.test', 
     'name': '测试集群管理员', 'occupation': '运维工程师', 'age': 31},
    {'role': 'admin', 'username': 'test_admin', 'email': 'admin@mtscos.test', 
     'name': '测试系统管理员', 'occupation': '系统管理员', 'age': 33},
    {'role': 'super_admin', 'username': 'test_superadmin', 'email': 'superadmin@mtscos.test', 
     'name': '测试超级管理员', 'occupation': '超级管理员', 'age': 34, 'super_admin_approved': 1},
    {'role': 'hardware_admin', 'username': 'test_hwadmin', 'email': 'hwadmin@mtscos.test', 
     'name': '测试硬件管理员', 'occupation': '硬件管理员', 'age': 36, 'hardware_admin_approved': 1}
]


def hash_password(password):
    """加密密码"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_test_users():
    """创建测试用户"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for role_info in ROLES:
                role = role_info['role']
                username = role_info['username']
                email = role_info['email']
                
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                existing = cursor.fetchone()
                
                now = datetime.now().timestamp()
                password_hash = hash_password(TEST_PASSWORD)
                
                if existing:
                    cursor.execute("""
                        UPDATE users SET password = ?, role = ?, email = ?, is_active = 1, 
                        super_admin_approved = ?, hardware_admin_approved = ?, updated_at = ?
                        WHERE username = ?
                    """, (
                        password_hash,
                        role,
                        email,
                        role_info.get('super_admin_approved', 0),
                        role_info.get('hardware_admin_approved', 0),
                        now,
                        username
                    ))
                    updated_count += 1
                    print(f"✓ 更新测试用户: {username} ({role})")
                else:
                    cursor.execute("""
                        INSERT INTO users (username, email, password, role, created_at, updated_at, 
                                          is_active, super_admin_approved, hardware_admin_approved,
                                          grade, student_type, education_level, school_type, 
                                          occupation, age)
                        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        username,
                        email,
                        password_hash,
                        role,
                        now,
                        now,
                        role_info.get('super_admin_approved', 0),
                        role_info.get('hardware_admin_approved', 0),
                        role_info.get('grade', ''),
                        role_info.get('student_type', ''),
                        role_info.get('education_level', ''),
                        role_info.get('school_type', ''),
                        role_info.get('occupation', ''),
                        role_info.get('age', 0)
                    ))
                    created_count += 1
                    print(f"✓ 创建测试用户: {username} ({role})")
            
            conn.commit()
            print(f"\n🎉 完成！创建: {created_count}, 更新: {updated_count}, 跳过: {skipped_count}")
            
            return True
    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return False


def verify_test_users():
    """验证测试用户"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            print("\n📋 验证测试用户:")
            for role_info in ROLES:
                cursor.execute("SELECT id, username, role, is_active FROM users WHERE username = ?", 
                              (role_info['username'],))
                result = cursor.fetchone()
                if result:
                    status = "✅" if result[3] == 1 else "❌"
                    print(f"  {status} {result[1]} - {result[2]} (ID: {result[0]})")
                else:
                    print(f"  ❌ {role_info['username']} - 不存在")
        
        return True
    except Exception as e:
        print(f"❌ 验证测试用户失败: {e}")
        return False


def print_test_accounts():
    """打印测试账号信息"""
    print("\n" + "="*60)
    print("          MTSCOS AI 测试账号信息")
    print("="*60)
    print(f"统一密码: {TEST_PASSWORD}")
    print("-"*60)
    print(f"{'用户名':<20} {'角色':<15} {'邮箱'}")
    print("-"*60)
    
    for role_info in ROLES:
        print(f"{role_info['username']:<20} {role_info['role']:<15} {role_info['email']}")
    
    print("-"*60)
    print("访问地址: http://localhost:8888/admin_app/login")
    print("="*60)


if __name__ == '__main__':
    print("🚀 开始创建测试用户...")
    
    if create_test_users():
        verify_test_users()
        print_test_accounts()
    else:
        sys.exit(1)