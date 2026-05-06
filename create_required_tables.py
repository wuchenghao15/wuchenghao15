#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据项目功能需求自动创建必要的后台数据库表"""

import sqlite3
import os
from datetime import datetime

class TableCreator:
    def __init__(self, db_path='app.db'):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    def table_exists(self, table_name):
        """检查表是否存在"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def create_table(self, table_name, create_sql):
        """创建表"""
        if self.table_exists(table_name):
            print(f"  ✅ 表 {table_name} 已存在，跳过")
            return False

        cursor = conn.cursor()
            cursor.execute(create_sql)
            conn.commit()
            print(f"  ✅ 表 {table_name} 创建成功")
            conn.close()
            return True
            print(f"  ❌ 表 {table_name} 创建失败: {str(e)}")
            conn.close()
            return False
    def create_all_required_tables(self):
        """创建所有必要的数据库表"""
        print("        根据项目功能需求创建必要的后台数据库表")
        print("="*70)

        created_count = 0
        skipped_count = 0

        print("\n[1] 系统日志表")
        sql = '''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            module TEXT,
            message TEXT NOT NULL,
            details TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            process_id INTEGER,
            thread_id INTEGER,
            ip_address TEXT,
            user_id INTEGER
        )
        '''
        if self.create_table('system_logs', sql):
            created_count += 1
        else:
            skipped_count += 1

        # 2. 操作审计表
        print("\n[2] 操作审计表")
        sql = '''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            success INTEGER DEFAULT 1,
            error_message TEXT
        )
        '''
            created_count += 1
            skipped_count += 1
        # 3. 任务调度表
        print("\n[3] 任务调度表")
        sql = '''
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            task_name TEXT UNIQUE NOT NULL,
            schedule TEXT NOT NULL,
            last_run TEXT,
            next_run TEXT,
            params TEXT DEFAULT '{}',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            enabled INTEGER DEFAULT 1
        )
        '''
        if self.create_table('scheduled_tasks', sql):
            created_count += 1
        else:
            skipped_count += 1

        # 4. 任务执行日志表
        print("\n[4] 任务执行日志表")
        sql = '''
        CREATE TABLE IF NOT EXISTS task_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            status TEXT DEFAULT 'running',
            end_time TEXT,
            output TEXT,
            error_message TEXT,
            FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id)
        )
        '''
        if self.create_table('task_executions', sql):
            created_count += 1
        else:
            skipped_count += 1

        # 5. 消息通知表
        print("\n[5] 消息通知表")
        sql = '''
        CREATE TABLE IF NOT EXISTS notifications (
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'unread',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            read_at TEXT
        )
            created_count += 1
        else:
            skipped_count += 1

        # 6. 文件管理表
        print("\n[6] 文件管理表")
        sql = '''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            filepath TEXT NOT NULL,
            mime_type TEXT,
            user_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        '''
        if self.create_table('files', sql):
        else:

        # 7. 系统监控表
        print("\n[7] 系统监控表")
        sql = '''
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            node_id TEXT
        )
        '''
        if self.create_table('system_metrics', sql):
        else:

        # 8. API访问日志表
        print("\n[8] API访问日志表")
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            ip_address TEXT,
            user_id INTEGER,
            response_body TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
        if self.create_table('api_access_logs', sql):
            skipped_count += 1

        # 9. 会话管理表
        print("\n[9] 会话管理表")
        sql = '''
        CREATE TABLE IF NOT EXISTS sessions (
            user_id INTEGER,
            username TEXT,
            created_at TEXT,
            last_activity TEXT,
            ip_address TEXT,
            user_agent TEXT,
            device_info TEXT
        '''
        if self.create_table('sessions', sql):
            created_count += 1
        else:
            skipped_count += 1

        print("\n[10] 权限管理表")
        sql = '''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permission_key TEXT UNIQUE NOT NULL,
            permission_name TEXT NOT NULL,
            description TEXT,
        )
        if self.create_table('permissions', sql):
            created_count += 1
        else:
            skipped_count += 1
        # 11. 角色权限关联表
        print("\n[11] 角色权限关联表")
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id TEXT,
            permission_key TEXT,
        )
        if self.create_table('role_permissions', sql):
            created_count += 1
        else:
            skipped_count += 1

        print("\n[12] 用户角色表")
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER,
            role_id TEXT,
            PRIMARY KEY (user_id, role_id)
        '''
        if self.create_table('user_roles', sql):
        else:
            skipped_count += 1
        # 13. 系统配置表（确保存在）
        print("\n[13] 系统配置表")
        sql = '''
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            description TEXT,
            data_type TEXT DEFAULT 'string',
            is_active INTEGER DEFAULT 1,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
        if self.create_table('system_config', sql):
            created_count += 1
        else:
            skipped_count += 1

        # 14. 系统事件表
        print("\n[14] 系统事件表")
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_subtype TEXT,
            details TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            source TEXT
        )
        '''
        if self.create_table('system_events', sql):
            created_count += 1
        else:
            skipped_count += 1

        # 15. 数据同步日志表
        sql = '''
        CREATE TABLE IF NOT EXISTS sync_logs (
            sync_type TEXT NOT NULL,
            source TEXT,
            target TEXT,
            success_count INTEGER DEFAULT 0,
            start_time TEXT,
            end_time TEXT,
            error_message TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
        if self.create_table('sync_logs', sql):
        else:
        # 16. AI模型执行日志表
        CREATE TABLE IF NOT EXISTS ai_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_name TEXT,
            task_type TEXT,
            output_data TEXT,
            status TEXT DEFAULT 'running',
            duration REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
        if self.create_table('ai_execution_logs', sql):
            created_count += 1
        else:
            skipped_count += 1

        print(f"        创建完成: {created_count} 个新表, {skipped_count} 个已存在")

        print("\n初始化默认数据...")
        cursor = conn.cursor()

        permissions = [
            ('system:config', '系统配置', '管理系统配置参数', 'system'),
            ('system:logs', '查看系统日志', '查看系统运行日志', 'system'),
            ('users:read', '查看用户', '查看用户列表', 'user'),
            ('users:delete', '删除用户', '删除用户账户', 'user'),
            ('ai:manage', '管理AI', '管理AI实例', 'ai'),
            ('ai:monitor', '监控AI', '监控AI状态', 'ai'),
            ('exam:create', '创建考试', '创建考试任务', 'exam'),
            ('exam:view', '查看考试', '查看考试信息', 'exam'),
            ('content:read', '读取内容', '读取系统内容', 'content'),
            ('content:write', '管理内容', '创建和修改内容', 'content')
        ]

        for key, name, desc, category in permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (permission_key, permission_name, description, category)
                VALUES (?, ?, ?, ?)
            ''', (key, name, desc, category))
        # 初始化角色数据
        roles = [
            ('admin', '系统管理员'),
            ('teacher', '教师'),
            ('student', '学生'),
        ]

        for role_id, name in roles:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (permission_key, permission_name, description, category)
                VALUES (?, ?, ?, ?)

        conn.commit()
        conn.close()
        print("  ✅ 默认权限数据初始化完成")

def main():
    result = creator.create_all_required_tables()

    main()
