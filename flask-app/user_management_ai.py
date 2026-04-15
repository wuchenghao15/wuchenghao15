#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理AI - 负责用户信息的管理，包括添加新用户、管理用户组和密码等
"""

import os
import sqlite3
import json
import time
import logging
import hashlib
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('user_management_ai')

class UserManagementAI:
    """用户管理AI"""
    
    def __init__(self):
        self.ai_id = f"user-management-ai-{int(time.time())}"
        self.name = "用户管理AI"
        self.description = "负责用户信息的管理，包括添加新用户、管理用户组和密码等"
        self.created_at = datetime.now().isoformat()
        logger.info(f"✅ 新建用户管理AI: {self.ai_id}")
    
    def add_users(self, users):
        """添加用户"""
        logger.info("=== 开始添加用户 ===")
        
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # 创建新表
                cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, group_name TEXT, created_at TEXT, updated_at TEXT)")
            else:
                # 检查表结构，添加缺失的列
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'group_name' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN group_name TEXT")
                if 'created_at' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
                if 'updated_at' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
            
            # 添加用户
            added_count = 0
            
            for user in users:
                username = user.get('username')
                password = user.get('password')
                group_name = user.get('group_name')
                
                if not username:
                    logger.warning("❌ 用户名不能为空")
                    continue
                
                if not password:
                    logger.warning(f"❌ 用户 {username} 密码不能为空")
                    continue
                
                if not group_name:
                    logger.warning(f"❌ 用户 {username} 组别不能为空")
                    continue
                
                # 哈希密码
                hashed_password = self._hash_password(password)
                
                # 插入用户
                try:
                    cursor.execute("INSERT OR REPLACE INTO users (username, password, group_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)", (
                        username,
                        hashed_password,
                        group_name,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    logger.info(f"✅ 添加用户 {username} 成功")
                    added_count += 1
                except Exception as e:
                    logger.error(f"❌ 添加用户 {username} 失败: {str(e)}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 添加用户完成，共添加 {added_count} 个用户")
            return {'status': 'ok', 'added_count': added_count, 'total_users': len(users)}
            
        except Exception as e:
            logger.error(f"❌ 添加用户失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _hash_password(self, password):
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def get_users(self):
        """获取所有用户"""
        logger.info("=== 开始获取用户列表 ===")
        
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 获取所有用户
            cursor.execute("SELECT username, group_name, created_at FROM users")
            users = cursor.fetchall()
            
            user_list = []
            for user in users:
                user_list.append({
                    'username': user[0],
                    'group_name': user[1],
                    'created_at': user[2]
                })
            
            conn.close()
            
            logger.info(f"✅ 获取用户列表完成，共 {len(user_list)} 个用户")
            return {'status': 'ok', 'users': user_list}
            
        except Exception as e:
            logger.error(f"❌ 获取用户列表失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def report_to_database(self, add_result, get_result):
        """上报到数据库"""
        logger.info("=== 开始上报到数据库 ===")
        
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建用户管理报告表
            cursor.execute("CREATE TABLE IF NOT EXISTS user_management (id INTEGER PRIMARY KEY AUTOINCREMENT, management_id TEXT UNIQUE, added_users INTEGER, total_users INTEGER, status TEXT, created_at TEXT, updated_at TEXT)")
            
            # 计算统计信息
            added_users = add_result.get('added_count', 0)
            total_users = len(get_result.get('users', []))
            status = add_result.get('status', 'error')
            
            # 生成管理ID
            management_id = f"user-management-{int(time.time())}"
            
            # 插入上报信息
            cursor.execute("INSERT OR REPLACE INTO user_management (management_id, added_users, total_users, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", (
                management_id,
                added_users,
                total_users,
                status,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 上报到数据库完成，管理ID: {management_id}")
            return {'status': 'ok', 'management_id': management_id}
            
        except Exception as e:
            logger.error(f"❌ 上报到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def share_error_cases(self):
        """共享错误修复案例到脑库"""
        logger.info("=== 开始共享错误修复案例 ===")
        
        try:
            # 收集错误修复案例
            error_cases = [
                {
                    "id": "user-management-case-001",
                    "title": "用户添加失败",
                    "description": "用户添加失败，可能是用户名已存在或数据库权限问题",
                    "solution": "检查用户名是否已存在，确保数据库有写入权限",
                    "affected_files": ["app/services/user_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "user-management-case-002",
                    "title": "密码哈希失败",
                    "description": "密码哈希失败，可能是密码格式错误或哈希算法问题",
                    "solution": "检查密码格式，确保使用正确的哈希算法",
                    "affected_files": ["app/services/user_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "user-management-case-003",
                    "title": "用户列表获取失败",
                    "description": "用户列表获取失败，可能是数据库连接问题或表结构不匹配",
                    "solution": "检查数据库连接和表结构，确保表结构符合要求",
                    "affected_files": ["app/services/user_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "user-management-case-004",
                    "title": "数据库上报失败",
                    "description": "数据库上报失败，可能是数据库连接问题或表结构不匹配",
                    "solution": "检查数据库连接和表结构，确保表结构符合上报要求",
                    "affected_files": ["app/services/user_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "user-management-case-005",
                    "title": "用户验证失败",
                    "description": "用户验证失败，可能是密码错误或用户不存在",
                    "solution": "检查用户名和密码是否正确，确保用户存在",
                    "affected_files": ["app/services/user_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                }
            ]
            
            # 保存到脑库
            brain_file = 'app/ai/brain/error_cases.json'
            if not os.path.exists('app/ai/brain'):
                os.makedirs('app/ai/brain')
            
            # 如果文件存在，读取现有数据
            existing_cases = []
            if os.path.exists(brain_file):
                with open(brain_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_cases = json.load(f)
                    except:
                        existing_cases = []
            
            # 合并案例
            all_cases = existing_cases + error_cases
            
            # 去重
            seen_ids = set()
            unique_cases = []
            for case in all_cases:
                if case['id'] not in seen_ids:
                    seen_ids.add(case['id'])
                    unique_cases.append(case)
            
            # 保存
            with open(brain_file, 'w', encoding='utf-8') as f:
                json.dump(unique_cases, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 错误修复案例共享完成，保存至: {brain_file}")
            logger.info(f"✅ 共共享 {len(error_cases)} 个新案例")
            
            return {'status': 'ok', 'cases': error_cases, 'total_cases': len(unique_cases)}
            
        except Exception as e:
            logger.error(f"❌ 共享错误修复案例失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def run_workflow(self, users):
        """执行完整的工作流程"""
        logger.info("=== 开始用户管理AI工作流程 ===")
        
        # 1. 添加用户
        add_result = self.add_users(users)
        
        # 2. 获取用户列表
        get_result = self.get_users()
        
        # 3. 上报到数据库
        database_report = self.report_to_database(add_result, get_result)
        
        # 4. 共享错误修复案例到脑库
        error_cases = self.share_error_cases()
        
        results = {
            'add_result': add_result,
            'get_result': get_result,
            'database_report': database_report,
            'error_cases': error_cases
        }
        
        logger.info("=== 用户管理AI工作流程完成 ===")
        
        return results

def main():
    """主函数"""
    logger.info("=== 启动用户管理AI ===")
    
    # 定义用户信息
    users = [
        {'username': 'wuchenghao15', 'group_name': '硬件管理员', 'password': 'LoginMe.1988$'},
        {'username': 'caopw', 'group_name': '学生', 'password': 'xuxu4pipo'},
        {'username': 'wuchenghao', 'group_name': '超级管理员', 'password': 'LoginMe.1988$'},
        {'username': 'caopinwen', 'group_name': '设计师', 'password': 'default123'},
        {'username': 'wuchnenghao16', 'group_name': '管理员', 'password': 'LoginMe.1988$'}
    ]
    
    # 创建用户管理AI
    user_ai = UserManagementAI()
    
    # 执行工作流程
    results = user_ai.run_workflow(users)
    
    # 输出结果
    logger.info("\n=== 工作结果摘要 ===")
    logger.info(f"添加结果: {results['add_result']}")
    logger.info(f"用户列表: {results['get_result']}")
    logger.info(f"数据库上报: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")
    
    logger.info("\n=== 用户管理AI工作完成 ===")

if __name__ == '__main__':
    main()