# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
内部通知系统 - 支持用户交流、留档日志和AI学习
"""

import os
import sys
import sqlite3
import json
import uuid
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


def log(message: str, symbol: str = '📢'):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} {message}")


def create_notification_tables():
    log('创建通知系统相关表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    tables = [
        '''CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            type TEXT DEFAULT 'system',
            sender_id INTEGER,
            recipient_id INTEGER,
            recipient_type TEXT DEFAULT 'user',
            priority INTEGER DEFAULT 1,
            status TEXT DEFAULT 'unread',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            metadata TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS notification_read (
            id TEXT PRIMARY KEY,
            notification_id TEXT,
            user_id INTEGER,
            read_at TEXT,
            FOREIGN KEY (notification_id) REFERENCES notifications(id)
        )''',
        
        '''CREATE TABLE IF NOT EXISTS notification_subscriptions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            channel_type TEXT,
            enabled INTEGER DEFAULT 1,
            settings TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS notification_channels (
            id TEXT PRIMARY KEY,
            channel_name TEXT UNIQUE,
            channel_description TEXT,
            notification_types TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS notification_logs (
            id TEXT PRIMARY KEY,
            notification_id TEXT,
            action TEXT,
            user_id INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )'''
    ]
    
    for sql in tables:
        try:
            cursor.execute(sql)
            log(f'  ✅ 表创建成功', '✅')
        except Exception as e:
            log(f'  ❌ 表创建失败: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'通知系统表创建完成', '✅')


def create_notification_rules():
    log('创建通知系统规则配置...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    rules = [
        ('notification_channels', '通知频道配置', '系统支持的通知频道', 'json', json.dumps([
            {'channel': 'system', 'name': '系统通知', 'description': '系统重要通知'},
            {'channel': 'exam', 'name': '考试通知', 'description': '考试相关通知'},
            {'channel': 'approval', 'name': '审批通知', 'description': '审批状态变更通知'},
            {'channel': 'message', 'name': '私信消息', 'description': '用户之间的私信交流'},
            {'channel': 'broadcast', 'name': '广播通知', 'description': '全站广播消息'}
        ])),
        
        ('notification_types', '通知类型配置', '支持的通知类型', 'json', json.dumps([
            {'type': 'system_alert', 'name': '系统警报', 'priority': 1},
            {'type': 'system_info', 'name': '系统信息', 'priority': 2},
            {'type': 'exam_start', 'name': '考试开始提醒', 'priority': 1},
            {'type': 'exam_end', 'name': '考试结束提醒', 'priority': 2},
            {'type': 'approval_pending', 'name': '待审批提醒', 'priority': 1},
            {'type': 'approval_approved', 'name': '审批通过', 'priority': 2},
            {'type': 'approval_rejected', 'name': '审批拒绝', 'priority': 2},
            {'type': 'message_received', 'name': '收到私信', 'priority': 1},
            {'type': 'broadcast', 'name': '广播消息', 'priority': 2},
            {'type': 'achievement', 'name': '成就解锁', 'priority': 3}
        ])),
        
        ('notification_priority', '优先级配置', '通知优先级定义', 'json', json.dumps([
            {'level': 1, 'name': '高优先级', 'color': '#fc8181', 'icon': '🔴'},
            {'level': 2, 'name': '中优先级', 'color': '#ed8936', 'icon': '🟡'},
            {'level': 3, 'name': '低优先级', 'color': '#48bb78', 'icon': '🟢'}
        ])),
        
        ('notification_retention_days', '保留天数', '通知保留天数', 'number', '90'),
        ('notification_auto_delete', '自动删除', '超过保留天数自动删除', 'boolean', 'true'),
        ('notification_max_per_user', '用户最大通知数', '单个用户最大通知数量', 'number', '1000'),
        ('notification_broadcast_limit', '广播限制', '每日最大广播次数', 'number', '10'),
        ('notification_enabled', '通知功能', '是否启用通知系统', 'boolean', 'true')
    ]
    
    for code, name, desc, rtype, value in rules:
        try:
            cursor.execute('SELECT id FROM approval_rules WHERE rule_code = ?', (code,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('UPDATE approval_rules SET rule_name = ?, rule_description = ?, rule_type = ?, rule_value = ? WHERE rule_code = ?', (name, desc, rtype, value, code))
            else:
                cursor.execute('INSERT INTO approval_rules (id, rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (str(uuid.uuid4()), code, name, desc, rtype, value, 1, 100))
            
            log(f'  ✅ {name}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'通知系统规则配置完成: {len(rules)} 条规则', '✅')


def create_notification_channels():
    log('创建通知频道数据...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    channels = [
        ('system', '系统通知', '系统重要通知和警报', json.dumps(['system_alert', 'system_info'])),
        ('exam', '考试通知', '考试相关通知和提醒', json.dumps(['exam_start', 'exam_end'])),
        ('approval', '审批通知', '审批状态变更通知', json.dumps(['approval_pending', 'approval_approved', 'approval_rejected'])),
        ('message', '私信消息', '用户之间的私信交流', json.dumps(['message_received'])),
        ('broadcast', '广播通知', '全站广播消息', json.dumps(['broadcast']))
    ]
    
    for name, desc, description, types in channels:
        try:
            cursor.execute('SELECT id FROM notification_channels WHERE channel_name = ?', (name,))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO notification_channels (id, channel_name, channel_description, notification_types) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), name, description, types))
            log(f'  ✅ {name}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'通知频道创建完成', '✅')


def main():
    print('\n' + '='*60)
    print('📢 内部通知系统创建')
    print('='*60 + '\n')
    
    create_notification_tables()
    create_notification_rules()
    create_notification_channels()
    
    print('\n' + '='*60)
    log('通知系统创建完成!', '✅')
    print('='*60 + '\n')


if __name__ == '__main__':
    main()
