# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建规则表并插入沙盒权限规则
"""

import os
import sqlite3
from contextlib import contextmanager
# JSON import removed - using database
import logging
import uuid
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def create_rules_table():
    """创建规则表(如果不存在)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            id TEXT PRIMARY KEY,
            rule_type TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            rule_content TEXT NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 5,
            enabled INTEGER DEFAULT 1,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ 规则表创建完成")

def insert_rule(rule):
    """插入规则到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM rules WHERE rule_name = ?", (rule['name'],))
    if cursor.fetchone():
        logger.warning(f"规则已存在,跳过: {rule['name']}")
        conn.close()
        return False

    rule_content = {
        "conditions": rule['conditions'],
        "actions": rule['actions']
    }

    cursor.execute('''
        INSERT INTO rules (
            id, rule_type, rule_name, rule_content, description,
            priority, enabled, version, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', (
        rule['id'],
        rule['type'],
        rule['name'],
        str(rule_content),
        rule['description'],
        rule['priority'],
        1 if rule['status'] == 'active' else 0,
        1
    ))

    conn.commit()
    conn.close()
    logger.info(f"✅ 规则插入成功: {rule['name']}")
    return True

def main():
    """主函数"""
    logger.info("开始创建规则并更新规则服务器...")

    create_rules_table()

    rules = [
        {
            "id": str(uuid.uuid4()),
            "name": "沙盒日志双备份规则",
            "type": "security",
            "description": "删除沙盒日志前必须自动双备份,备份记录不可修改删除",
            "conditions": [
                {
                    "eventType": "delete_sandbox_logs",
                    "userRole": "hardware_admin"
                }
            ],
            "actions": [
                {
                    "type": "dual_backup",
                    "parameters": {
                        "backupType": "log",
                        "destinations": ["/backups/sandbox_logs/primary", "/backups/sandbox_logs/secondary"],
                        "compression": True,
                        "encryption": True
                    }
                },
                {
                    "type": "delete",
                    "parameters": {
                        "target": "sandbox_logs"
                    }
                }
            ],
            "priority": 15,
            "status": "active"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "沙盒参数修改审批规则",
            "type": "approval",
            "description": "修改沙盒参数需要审批",
            "conditions": [
                {
                    "eventType": "modify_sandbox_parameters",
                    "userRole": "admin"
                }
            ],
            "actions": [
                {
                    "type": "require_approval",
                    "parameters": {
                        "approvers": ["superadmin", "hardware_admin"]
                    }
                }
            ],
            "priority": 10,
            "status": "active"
        }
    ]

    for rule in rules:
        insert_rule(rule)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rules")
    rule_count = cursor.fetchone()[0]
    conn.close()
    logger.info(f"✅ 规则创建完成,当前规则数量: {rule_count}")
    logger.info("规则服务器更新完成!")

if __name__ == "__main__":
    main()
