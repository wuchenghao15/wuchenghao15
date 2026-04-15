#!/usr/bin/env python3
"""
验证数据库状态脚本
检查上传的数据、表结构和规则
"""

import os
import sqlite3
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def verify_database():
    """验证数据库状态"""
    logger.info("开始验证数据库状态")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        logger.info("数据库连接成功")
        
        # 检查local_data_uploads表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='local_data_uploads'")
        if cursor.fetchone():
            logger.info("✅ local_data_uploads表已创建")
            
            # 查询上传的数据数量
            cursor.execute("SELECT COUNT(*) FROM local_data_uploads")
            count = cursor.fetchone()[0]
            logger.info(f"✅ 已上传 {count} 个JSON文件")
            
            # 查询按类型分布
            cursor.execute("SELECT data_type, COUNT(*) FROM local_data_uploads GROUP BY data_type")
            types = cursor.fetchall()
            for data_type, type_count in types:
                logger.info(f"   - {data_type}: {type_count} 个")
        else:
            logger.error("❌ local_data_uploads表不存在")
        
        # 检查规则表（如果存在）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%rule%'")
        rule_tables = cursor.fetchall()
        if rule_tables:
            logger.info("✅ 规则相关表已创建:")
            for table in rule_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                rule_count = cursor.fetchone()[0]
                logger.info(f"   - {table[0]}: {rule_count} 条记录")
        else:
            logger.warning("⚠️  未找到规则相关表")
        
        # 检查备份目录
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        if os.path.exists(backup_dir):
            logger.info("✅ 备份目录已存在")
            primary_backup = os.path.join(backup_dir, 'primary')
            secondary_backup = os.path.join(backup_dir, 'secondary')
            if os.path.exists(primary_backup):
                primary_files = [f for f in os.listdir(primary_backup) if f.endswith('.db')]
                logger.info(f"   - 主要备份文件: {len(primary_files)} 个")
            if os.path.exists(secondary_backup):
                secondary_files = [f for f in os.listdir(secondary_backup) if f.endswith('.db')]
                logger.info(f"   - 次要备份文件: {len(secondary_files)} 个")
        
        conn.close()
        logger.info("数据库验证完成")
        return True
    except Exception as e:
        logger.error(f"数据库验证失败: {str(e)}")
        return False

if __name__ == "__main__":
    verify_database()