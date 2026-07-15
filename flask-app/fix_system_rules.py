#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def create_system_rules_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT NOT NULL UNIQUE,
                rule_name TEXT NOT NULL,
                rule_value TEXT,
                rule_type TEXT DEFAULT 'system',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM system_rules')
        if cursor.fetchone()[0] == 0:
            default_rules = [
                ('SYS_VERSION', '系统版本', '10.0.0', 'system', '当前系统版本号', 1),
                ('SYS_NAME', '系统名称', 'MTSCOS AI', 'system', '系统显示名称', 1),
                ('MAX_UPLOAD_SIZE', '最大上传大小', '52428800', 'system', '文件上传最大限制(字节)', 1),
                ('SESSION_TIMEOUT', '会话超时时间', '3600', 'system', '用户会话超时时间(秒)', 1),
                ('AI_ENABLED', 'AI功能启用', '1', 'system', '是否启用AI功能', 1),
                ('LOG_LEVEL', '日志级别', 'INFO', 'system', '系统日志级别', 1),
                ('DEBUG_MODE', '调试模式', '0', 'system', '是否启用调试模式', 0),
                ('MAINTENANCE_MODE', '维护模式', '0', 'system', '系统维护模式', 0),
                ('ALLOW_REGISTRATION', '允许注册', '1', 'system', '是否允许用户注册', 1),
                ('EMAIL_NOTIFICATION', '邮件通知', '1', 'system', '是否启用邮件通知', 1),
                ('MAX_LOGIN_ATTEMPTS', '最大登录尝试次数', '5', 'security', '允许的最大登录尝试次数', 1),
                ('LOCKOUT_DURATION', '账户锁定时长', '900', 'security', '账户锁定时长(秒)', 1),
                ('PASSWORD_MIN_LENGTH', '密码最小长度', '8', 'security', '密码最小长度', 1),
                ('PASSWORD_COMPLEXITY', '密码复杂度', '1', 'security', '是否启用密码复杂度要求', 1),
                ('EXAM_MAX_DURATION', '考试最大时长', '7200', 'exam', '考试最大时长(秒)', 1),
                ('EXAM_AUTO_SUBMIT', '考试自动提交', '1', 'exam', '超时是否自动提交', 1),
                ('GRADING_AUTO', '自动批改', '1', 'exam', '是否启用自动批改', 1),
                ('LEARNING_PATH_ENABLED', '学习路径启用', '1', 'learning', '是否启用智能学习路径', 1),
                ('RECOMMENDATION_ENABLED', '推荐功能启用', '1', 'learning', '是否启用智能推荐', 1),
                ('WARNING_SYSTEM_ENABLED', '预警系统启用', '1', 'learning', '是否启用学习预警系统', 1),
            ]
            
            for rule in default_rules:
                cursor.execute('''
                    INSERT INTO system_rules (rule_code, rule_name, rule_value, rule_type, description, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', rule)
            
            print("✓ 已初始化默认系统规则")
        
        conn.commit()
        conn.close()
        print("✓ system_rules 表创建成功")
        return True
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        return False

def check_system_rules_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_rules'")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print("✓ system_rules 表已存在")
            return True
        else:
            print("✗ system_rules 表不存在")
            return False
    except Exception as e:
        print(f"✗ 检查表失败: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("修复 system_rules 表")
    print("=" * 50)
    
    if not check_system_rules_table():
        create_system_rules_table()
    else:
        print("表已存在，无需修复")
    
    print("=" * 50)
    print("修复完成")
    print("=" * 50)