#!/usr/bin/env python3
"""
高危敏感设置数据库初始化脚本
创建必要的数据库表和默认数据
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def init_database():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("正在创建数据库表...")
    
    # 1. 高危敏感设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensitive_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            setting_key TEXT NOT NULL UNIQUE,
            setting_name TEXT NOT NULL,
            setting_value TEXT,
            default_value TEXT,
            value_type TEXT DEFAULT 'string',
            description TEXT,
            is_dangerous BOOLEAN DEFAULT 0,
            requires_restart BOOLEAN DEFAULT 1,
            requires_approval BOOLEAN DEFAULT 0,
            approval_status TEXT DEFAULT 'none',
            approved_by INTEGER,
            approval_date TIMESTAMP,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (approved_by) REFERENCES users(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # 2. 设置审批记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS setting_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_id INTEGER NOT NULL,
            requester_id INTEGER NOT NULL,
            requester_role TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            approver_id INTEGER,
            approver_role TEXT,
            approval_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (setting_id) REFERENCES sensitive_settings(id),
            FOREIGN KEY (requester_id) REFERENCES users(id),
            FOREIGN KEY (approver_id) REFERENCES users(id)
        )
    ''')
    
    # 3. 数据库备份记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS database_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_type TEXT NOT NULL,
            backup_path TEXT NOT NULL,
            backup_size INTEGER,
            trigger_reason TEXT,
            triggered_by INTEGER,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (triggered_by) REFERENCES users(id)
        )
    ''')
    
    # 4. 服务重启记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_restarts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restart_type TEXT NOT NULL,
            services_affected TEXT,
            reason TEXT,
            triggered_by INTEGER,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (triggered_by) REFERENCES users(id)
        )
    ''')
    
    # 5. 系统操作日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL,
            operation_category TEXT,
            description TEXT,
            details TEXT,
            user_id INTEGER,
            user_role TEXT,
            ip_address TEXT,
            status TEXT DEFAULT 'success',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    print("✓ 数据库表创建完成")
    
    return conn

def insert_default_settings(conn):
    """插入默认的高危敏感设置"""
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM sensitive_settings")
    if cursor.fetchone()[0] > 0:
        print("✓ 高危设置数据已存在，跳过初始化")
        return
    
    print("正在插入默认高危设置...")
    
    # 默认的高危敏感设置
    default_settings = [
        # 系统核心设置
        ('system', 'DEBUG_MODE', '调试模式', 'false', 'false', 'boolean', 
         '启用系统调试模式（高危：可能暴露敏感信息）', True, True, False),
        ('system', 'MAINTENANCE_MODE', '维护模式', 'false', 'false', 'boolean',
         '启用系统维护模式（会阻止所有用户访问）', True, True, False),
        ('system', 'ALLOW_REMOTE_ACCESS', '远程访问', 'true', 'true', 'boolean',
         '允许远程访问系统（高危：安全风险）', True, True, False),
        ('system', 'MAX_CONNECTIONS', '最大连接数', '1000', '1000', 'integer',
         '系统最大并发连接数', True, True, False),
        
        # 数据库设置
        ('database', 'AUTO_BACKUP', '自动备份', 'true', 'true', 'boolean',
         '启用自动数据库备份', False, False, False),
        ('database', 'BACKUP_INTERVAL', '备份间隔（分钟）', '60', '60', 'integer',
         '自动备份的时间间隔', False, False, False),
        ('database', 'ALLOW_DIRECT_SQL', '直接SQL执行', 'false', 'false', 'boolean',
         '允许执行直接SQL命令（极高危：可能导致数据损坏）', True, True, True),
        ('database', 'DB_POOL_SIZE', '数据库连接池大小', '10', '10', 'integer',
         '数据库连接池的最大连接数', True, True, False),
        
        # 安全设置
        ('security', 'ENCRYPTION_LEVEL', '加密级别', 'high', 'high', 'string',
         '数据加密级别（low/medium/high）', True, True, False),
        ('security', 'SESSION_TIMEOUT', '会话超时（秒）', '3600', '3600', 'integer',
         '用户会话超时时间', False, False, False),
        ('security', 'ALLOW_API_KEY_REGEN', 'API密钥重新生成', 'true', 'true', 'boolean',
         '允许用户重新生成API密钥', False, False, False),
        ('security', 'FORCE_2FA', '强制双因素认证', 'false', 'false', 'boolean',
         '强制所有用户启用双因素认证', True, True, False),
        ('security', 'IP_WHITELIST_ENABLED', 'IP白名单', 'false', 'false', 'boolean',
         '启用IP白名单访问控制', True, True, False),
        
        # AI员工设置
        ('ai_employee', 'AUTO_START_AI', '自动启动AI员工', 'true', 'true', 'boolean',
         '系统启动时自动启动所有AI员工', False, True, False),
        ('ai_employee', 'MAX_AI_INSTANCES', '最大AI实例数', '10', '10', 'integer',
         '允许同时运行的最大AI员工实例数', True, True, False),
        ('ai_employee', 'AI_MEMORY_LIMIT', 'AI内存限制（MB）', '512', '512', 'integer',
         '每个AI员工的最大内存使用限制', True, True, False),
        ('ai_employee', 'ALLOW_AI_NETWORK', 'AI网络访问', 'false', 'false', 'boolean',
         '允许AI员工访问外部网络（高危：安全风险）', True, True, True),
        
        # 性能设置
        ('performance', 'CACHE_ENABLED', '缓存启用', 'true', 'true', 'boolean',
         '启用系统缓存', False, False, False),
        ('performance', 'CACHE_SIZE', '缓存大小（MB）', '100', '100', 'integer',
         '系统缓存的最大大小', False, False, False),
        ('performance', 'ASYNC_OPERATIONS', '异步操作', 'true', 'true', 'boolean',
         '启用异步操作处理', False, True, False),
        
        # 网络设置
        ('network', 'HTTP_PORT', 'HTTP端口', '8888', '8888', 'integer',
         'HTTP服务监听端口', True, True, False),
        ('network', 'HTTPS_ENABLED', 'HTTPS启用', 'false', 'false', 'boolean',
         '启用HTTPS（需要证书）', True, True, False),
        ('network', 'CORS_ENABLED', 'CORS启用', 'true', 'true', 'boolean',
         '启用跨域资源共享', False, False, False),
        ('network', 'RATE_LIMIT', '请求速率限制', '100', '100', 'integer',
         '每分钟最大请求数', False, False, False),
    ]
    
    for setting in default_settings:
        cursor.execute('''
            INSERT INTO sensitive_settings 
            (category, setting_key, setting_name, setting_value, default_value, value_type, 
             description, is_dangerous, requires_restart, requires_approval)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', setting)
    
    conn.commit()
    print(f"✓ 已插入 {len(default_settings)} 个默认设置")

def main():
    """主函数"""
    print("=" * 60)
    print("高危敏感设置数据库初始化")
    print("=" * 60)
    
    # 初始化数据库表
    conn = init_database()
    
    # 插入默认设置
    insert_default_settings(conn)
    
    # 关闭连接
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
    print("\n已创建的表：")
    print("  - sensitive_settings (高危敏感设置)")
    print("  - setting_approvals (设置审批记录)")
    print("  - database_backups (数据库备份记录)")
    print("  - service_restarts (服务重启记录)")
    print("  - system_operation_logs (系统操作日志)")
    print("\n下一步：")
    print("  1. 更新硬件设置页面UI")
    print("  2. 实现权限控制和审批流程")
    print("  3. 实现数据库备份功能")
    print("  4. 实现服务重启功能")

if __name__ == "__main__":
    main()
