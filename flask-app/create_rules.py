#!/usr/bin/env python3
"""
创建规则表并插入沙盒权限规则
"""

import os
import sqlite3
import json
import logging
import uuid

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def create_rules_table():
    """创建规则表（如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建规则表
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
    
    # 检查规则是否已存在
    cursor.execute("SELECT id FROM rules WHERE id = ?", (rule['id'],))
    if cursor.fetchone():
        logger.warning(f"规则已存在，跳过: {rule['name']}")
        conn.close()
        return False
    
    # 构建规则内容
    rule_content = {
        "conditions": rule['conditions'],
        "actions": rule['actions']
    }
    
    # 插入规则
    cursor.execute('''
    INSERT INTO rules (
        id, rule_type, rule_name, rule_content, description, 
        priority, enabled, version, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ''', (
        rule['id'],
        rule['type'],
        rule['name'],
        json.dumps(rule_content),
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
    
    # 创建规则表
    create_rules_table()
    
    # 定义沙盒日志双备份规则
    sandbox_log_backup_rule = {
        "id": str(uuid.uuid4()),
        "name": "沙盒日志双备份规则",
        "type": "security",
        "description": "删除沙盒日志前必须自动双备份，备份记录不可修改删除",
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
                    "source": "sandbox_logs",
                    "destinations": ["/backups/sandbox_logs/primary", "/backups/sandbox_logs/secondary"],
                    "compression": True,
                    "encryption": True,
                    "immutable": True
                }
            },
            {
                "type": "delete",
                "parameters": {
                    "target": "sandbox_logs"
                }
            }
        ],
        "priority": 15,  # URGENT
        "status": "active"
    }
    
    # 定义沙盒参数修改审批规则
    sandbox_param_approval_rule = {
        "id": str(uuid.uuid4()),
        "name": "沙盒参数修改审批规则",
        "type": "business",
        "description": "管理员修改沙盒参数需要管理员以上权限审批",
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
                    "approvers": ["superadmin", "hardware_admin"],
                    "approvalType": "any"
                }
            }
        ],
        "priority": 10,  # HIGH
        "status": "active"
    }
    
    # 插入规则
    rules = [sandbox_log_backup_rule, sandbox_param_approval_rule]
    
    for rule in rules:
        insert_rule(rule)
    
    # 验证规则是否插入成功
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rules")
    rule_count = cursor.fetchone()[0]
    conn.close()
    
    logger.info(f"✅ 规则创建完成，当前规则数量: {rule_count}")
    logger.info("规则服务器更新完成！")

if __name__ == "__main__":
    main()