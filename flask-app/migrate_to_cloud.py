# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
云端数据迁移脚本
用于将本地数据库数据迁移到云端数据库
支持的数据库类型:SQLite -> MySQL/PostgreSQL
"""

import os
import sys
import logging
import argparse
import sqlite3
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migrate_to_cloud.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('migrate_to_cloud')

DB_DRIVERS = {
    'sqlite': None,
    'mysql': None,
    'postgresql': None
}

try:
    DB_DRIVERS['sqlite'] = sqlite3
    logger.info("SQLite驱动加载成功")
except ImportError:
    logger.error("SQLite驱动加载失败")
    sys.exit(1)

try:
    import mysql.connector
    DB_DRIVERS['mysql'] = mysql.connector
    logger.info("MySQL驱动加载成功")
except ImportError:
    logger.warning("MySQL驱动加载失败,MySQL数据库不可用")

try:
    import psycopg2
    DB_DRIVERS['postgresql'] = psycopg2
    logger.info("PostgreSQL驱动加载成功")
except ImportError:
    logger.warning("PostgreSQL驱动加载失败,PostgreSQL数据库不可用")

class CloudMigration:
    """云端数据迁移类"""

    def __init__(self, local_db_path, cloud_db_type, cloud_db_config):
        """初始化迁移器

        Args:
            local_db_path: 本地SQLite数据库路径
            cloud_db_type: 云端数据库类型 (mysql/postgresql)
            cloud_db_config: 云端数据库配置
        """
        self.local_db_path = local_db_path
        self.cloud_db_type = cloud_db_type
        self.cloud_db_config = cloud_db_config

        self.table_mappings = {
            'user': 'user',
            'system_config': 'system_config',
            'ai_config': 'ai_config',
            'ai_db_adapter': 'ai_db_adapter',
            'ai_instance': 'ai_instance',
            'user_japanese_levels': 'user_japanese_levels',
            'user_groups': 'user_groups',
            'user_group_members': 'user_group_members'
        }

        self.data_type_mappings = {
            'sqlite': {
                'INTEGER': 'INT',
                'TEXT': 'VARCHAR(255)',
                'REAL': 'FLOAT',
                'BLOB': 'BLOB',
                'BOOLEAN': 'BOOLEAN'
            }
        }

    def get_local_tables(self):
        """获取本地数据库中的所有表"""
        conn = DB_DRIVERS['sqlite'].connect(self.local_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        conn.close()
        return tables

    def get_table_schema(self, table_name):
        """获取表的结构"""
        conn = DB_DRIVERS['sqlite'].connect(self.local_db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema = cursor.fetchall()
        conn.close()

        schema_info = []
        for col in schema:
            col_info = {
                'name': col[1],
                'type': col[2],
                'notnull': col[3],
                'default': col[4],
                'pk': col[5]
            }
            schema_info.append(col_info)
        return schema_info

    def get_table_data(self, table_name):
        """获取表中的所有数据"""
        conn = DB_DRIVERS['sqlite'].connect(self.local_db_path)
        conn.row_factory = DB_DRIVERS['sqlite'].Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name};")
        data = cursor.fetchall()
        conn.close()
        return data

    def create_cloud_connection(self):
        """创建云端数据库连接"""
        if self.cloud_db_type == 'mysql':
            if not DB_DRIVERS['mysql']:
                raise Exception("MySQL驱动未加载")

            conn = DB_DRIVERS['mysql'].connect(
                host=self.cloud_db_config['host'],
                port=self.cloud_db_config['port'],
                user=self.cloud_db_config['user'],
                password=self.cloud_db_config['password'],
                database=self.cloud_db_config['database']
            )
            return conn

        elif self.cloud_db_type == 'postgresql':
            if not DB_DRIVERS['postgresql']:
                raise Exception("PostgreSQL驱动未加载")

            conn = DB_DRIVERS['postgresql'].connect(
                host=self.cloud_db_config['host'],
                port=self.cloud_db_config['port'],
                user=self.cloud_db_config['user'],
                password=self.cloud_db_config['password'],
                dbname=self.cloud_db_config['database']
            )
            return conn

        else:
            raise Exception(f"不支持的数据库类型: {self.cloud_db_type}")

    def create_cloud_table(self, conn, table_name, schema):
        """在云端数据库创建表"""
        cursor = conn.cursor()

        columns = []
        for col in schema:
            col_type = self.data_type_mappings['sqlite'].get(col['type'], col['type'])

            if col['pk'] == 1:
                if self.cloud_db_type == 'mysql':
                    col_def = f"{col['name']} {col_type} AUTO_INCREMENT"
                elif self.cloud_db_type == 'postgresql':
                    col_def = f"{col['name']} SERIAL"
                else:
                    col_def = f"{col['name']} {col_type}"
            else:
                col_def = f"{col['name']} {col_type}"

            if col['notnull']:
                col_def += " NOT NULL"

            if col['default'] is not None:
                col_def += f" DEFAULT {col['default']}"

            columns.append(col_def)

        pk_cols = [col['name'] for col in schema if col['pk']]
        if pk_cols:
            columns.append(f"PRIMARY KEY ({', '.join(pk_cols)})")

        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"

        logger.info(f"创建表 {table_name}: {create_table_sql}")
        cursor.execute(create_table_sql)
        cursor.close()

    def migrate_table_data(self, conn, table_name, data):
        """迁移表数据"""
        if not data:
            logger.info(f"表 {table_name} 没有数据需要迁移")
            return

        cursor = conn.cursor()

        columns = list(data[0].keys())

        if self.cloud_db_type == 'mysql':
            placeholders = ', '.join(['%s'] * len(columns))
        elif self.cloud_db_type == 'postgresql':
            placeholders = ', '.join(['%s'] * len(columns))
        else:
            placeholders = ', '.join(['?'] * len(columns))

        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            values = [tuple(row[col] for col in columns) for row in batch]

            logger.info(f"迁移表 {table_name} 的数据,批次 {i//batch_size + 1}/{(len(data) + batch_size - 1)//batch_size}")
            cursor.executemany(insert_sql, values)
            conn.commit()

        cursor.close()
        logger.info(f"表 {table_name} 的数据迁移完成,共迁移 {len(data)} 条记录")

    def migrate(self):
        """执行数据迁移"""
        logger.info("开始数据迁移...")
        logger.info(f"本地数据库: {self.local_db_path}")
        logger.info(f"云端数据库类型: {self.cloud_db_type}")
        logger.info(f"云端数据库: {self.cloud_db_config['database']}@{self.cloud_db_config['host']}:{self.cloud_db_config['port']}")

        local_tables = self.get_local_tables()

        cloud_conn = self.create_cloud_connection()
        try:
            for table_name in local_tables:
                if table_name not in self.table_mappings:
                    logger.warning(f"表 {table_name} 不在映射列表中,跳过迁移")
                    continue

                cloud_table_name = self.table_mappings[table_name]
                logger.info(f"开始迁移表 {table_name} -> {cloud_table_name}")

                schema = self.get_table_schema(table_name)
                logger.info(f"表 {table_name} 的结构: {schema}")

                self.create_cloud_table(cloud_conn, cloud_table_name, schema)

                data = self.get_table_data(table_name)
                logger.info(f"表 {table_name} 共有 {len(data)} 条记录")

                self.migrate_table_data(cloud_conn, cloud_table_name, data)

                logger.info(f"表 {table_name} -> {cloud_table_name} 迁移完成")

            logger.info("数据迁移全部完成!")

        except Exception as e:
            logger.error(f"数据迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            cloud_conn.rollback()
            sys.exit(1)
        finally:
            cloud_conn.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='云端数据迁移脚本')
    parser.add_argument('--local-db', required=True, help='本地SQLite数据库路径')
    parser.add_argument('--cloud-type', required=True, choices=['mysql', 'postgresql'], help='云端数据库类型')
    parser.add_argument('--cloud-host', required=True, help='云端数据库主机')
    parser.add_argument('--cloud-port', required=True, type=int, help='云端数据库端口')
    parser.add_argument('--cloud-user', required=True, help='云端数据库用户名')
    parser.add_argument('--cloud-password', required=True, help='云端数据库密码')
    parser.add_argument('--cloud-db', required=True, help='云端数据库名称')
    args = parser.parse_args()

    if not DB_DRIVERS[args.cloud_type]:
        logger.error(f"云端数据库类型 {args.cloud_type} 驱动未加载")
        sys.exit(1)

    cloud_config = {
        'host': args.cloud_host,
        'port': args.cloud_port,
        'user': args.cloud_user,
        'password': args.cloud_password,
        'database': args.cloud_db
    }

    migrator = CloudMigration(
        local_db_path=args.local_db,
        cloud_db_type=args.cloud_type,
        cloud_db_config=cloud_config
    )

    migrator.migrate()

if __name__ == '__main__':
    main()
