# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复记录器 - 记录所有修复操作到数据库
"""

import sqlite3
import time
import os
from datetime import datetime
from app.utils.logging import logger
import logging


class FixLogger:
    """修复记录器"""

    def __init__(self, db_path="fix_logs.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fix_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    error_type TEXT,
                    fix_description TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path ON fix_logs(file_path)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON fix_logs(status)
            """)
            
            conn.commit()
            conn.close()
            logger.info("修复记录数据库初始化完成")
        except Exception as e:
            logger.error(f"初始化修复记录数据库失败: {str(e)}")

    def log_fix(self, file_path, error_type, fix_description, status="success"):
        """记录修复操作"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO fix_logs (file_path, error_type, fix_description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                error_type,
                fix_description,
                status,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"已记录修复: {file_path} - {error_type}")
        except Exception as e:
            logger.error(f"记录修复失败: {str(e)}")

    def get_all_fixes(self, status=None, limit=100):
        """获取所有修复记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT id, file_path, error_type, fix_description, status, created_at
                    FROM fix_logs
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (status, limit))
            else:
                cursor.execute("""
                    SELECT id, file_path, error_type, fix_description, status, created_at
                    FROM fix_logs
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            fixes = []
            for row in results:
                fixes.append({
                    "id": row[0],
                    "file_path": row[1],
                    "error_type": row[2],
                    "fix_description": row[3],
                    "status": row[4],
                    "created_at": row[5]
                })
            
            return fixes
        except Exception as e:
            logger.error(f"获取修复记录失败: {str(e)}")
            return []

    def get_fix_stats(self):
        """获取修复统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM fix_logs")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT status, COUNT(*) FROM fix_logs GROUP BY status")
            status_counts = cursor.fetchall()
            
            conn.close()
            
            stats = {"total": total}
            for status, count in status_counts:
                stats[status] = count
            
            return stats
        except Exception as e:
            logger.error(f"获取修复统计失败: {str(e)}")
            return {"total": 0}


# 创建全局实例
fix_logger = FixLogger()
