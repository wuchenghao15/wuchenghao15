# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复系统配置和数据库表问题
"""

import os
import sqlite3
from contextlib import contextmanager
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_system_issues')

def fix_system_config():
    """修复 SystemConfig 模型"""
    logger.info("修复 SystemConfig 模型...")

    config_model_path = 'app/models/system_config.py'
    if os.path.exists(config_model_path):
        with open(config_model_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'def get_all_configs' not in content:
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.strip() == 'class SystemConfig:':
                    new_lines.append('    @classmethod')
                    new_lines.append('    def get_all_configs(cls):')
                    new_lines.append('        """获取所有配置"""')
                    new_lines.append('        return {}')
                    new_lines.append('')

            content = '\n'.join(new_lines)

            with open(config_model_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info("修复 SystemConfig 模型")
        else:
            logger.info("SystemConfig 模型已包含 get_all_configs 方法")
    else:
        logger.warning(f"配置模型文件不存在: {config_model_path}")

def fix_user_snapshots_table():
    """修复用户快照表"""
    logger.info("修复用户快照表...")

    try:
        db_path = 'data/mtscos_ai_project.db'
        if not os.path.exists('data'):
            os.makedirs('data')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            session_id TEXT,
            snapshot_data TEXT,
            timestamp TEXT,
            snapshot_type TEXT,
            status TEXT,
            data TEXT,
            created_at TEXT,
            updated_at TEXT
            )
        ''')

        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_user_id ON user_snapshots(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_session_id ON user_snapshots(session_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_timestamp ON user_snapshots(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_type ON user_snapshots(snapshot_type)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_status ON user_snapshots(status)'
        ]

        for idx_sql in indexes:
            cursor.execute(idx_sql)

        conn.commit()
        conn.close()

        logger.info("修复用户快照表和索引")

    except Exception as e:
        logger.error(f"修复用户快照表失败: {str(e)}")

def main():
    """主函数"""
    logger.info("=== 开始修复系统问题 ===")

    fix_system_config()
    fix_user_snapshots_table()

    logger.info("=== 系统问题修复完成 ===")

if __name__ == '__main__':
    main()
