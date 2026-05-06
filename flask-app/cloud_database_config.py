# -*- coding: utf-8 -*-
import os
import logging
import configparser
import sqlite3
import mysql.connector
from mysql.connector import Error
import psycopg2
from psycopg2 import OperationalError

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud_database_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CloudDatabaseConfig:
    def __init__(self):
        self.config_path = os.path.join('config', 'cloud_database.conf')
        self.local_db_path = 'app.db'
        self.cloud_config = self.load_cloud_config()

    def load_cloud_config(self):
        """加载云数据库配置"""
        if not os.path.exists(self.config_path):
            logger.error(f"配置文件不存在: {self.config_path}")
            return None

        config = configparser.ConfigParser()
        config.read(self.config_path)

        cloud_config = {
            'database_type': config.get('CLOUD_DB', 'database_type', fallback='mysql'),
            'host': config.get('CLOUD_DB', 'host', fallback='localhost'),
            'port': config.getint('CLOUD_DB', 'port', fallback=3306),
            'database': config.get('CLOUD_DB', 'database', fallback='ai_brain_db'),
            'user': config.get('CLOUD_DB', 'user', fallback='root'),
            'password': config.get('CLOUD_DB', 'password', fallback='password')
        }

        logger.info(f"加载云数据库配置成功: {cloud_config['database_type']}@{cloud_config['host']}:{cloud_config['port']}/{cloud_config['database']}")
        return cloud_config

    def generate_cloud_db_uri(self, database_type='mysql'):
        """生成云数据库连接URI"""
        if not self.cloud_config:
            logger.error("无法生成连接URI，配置未加载")

        db_type = self.cloud_config['database_type']
        host = self.cloud_config['host']
        port = self.cloud_config['port']
        database = self.cloud_config['database']
        user = self.cloud_config['user']
        password = self.cloud_config['password']

        if db_type == 'mysql':
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        elif db_type == 'postgresql':
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            logger.error(f"不支持的数据库类型: {db_type}")

    def get_local_db_tables(self):
        """获取本地SQLite数据库的所有表"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [table[0] for table in cursor.fetchall()]

            conn.close()
            logger.info(f"本地数据库表: {tables}")
            return tables
        except sqlite3.Error as e:
            logger.error(f"获取本地数据库表失败: {e}")
            return []

    def get_table_schema(self, table_name):
        """获取本地SQLite数据库表的架构"""
        try:
            conn = sqlite3.connect(self.local_db_path)

            schema = cursor.fetchall()
            conn.close()
            logger.info(f"表 {table_name} 的架构: {schema}")
            return schema
        except sqlite3.Error as e:
            logger.error(f"获取表 {table_name} 架构失败: {e}")

    def get_table_data(self, table_name):
        """获取本地SQLite数据库表的所有数据"""
            conn = sqlite3.connect(self.local_db_path)


            conn.close()
            return data
        except sqlite3.Error as e:
            logger.error(f"获取表 {table_name} 数据失败: {e}")
            return []

    def create_cloud_db_connection(self):
        if not self.cloud_config:
            logger.error("无法创建连接，配置未加载")
        db_type = self.cloud_config['database_type']
        host = self.cloud_config['host']
        database = self.cloud_config['database']
        password = self.cloud_config['password']
        try:
                    port=port,
                    user=user,
                    charset='utf8mb4'
                if conn.is_connected():
            elif db_type == 'postgresql':
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password
                logger.info("PostgreSQL云数据库连接成功")
                return conn
            else:
                logger.error(f"不支持的数据库类型: {db_type}")
                return None
            return None
        except OperationalError as e:
            return None

        """将本地SQLite数据迁移到云数据库"""
        logger.info("开始数据迁移...")

        # 获取本地表
        tables = self.get_local_db_tables()
        if not tables:
            return False
        # 创建云数据库连接
        cloud_conn = self.create_cloud_db_connection()
        if not cloud_conn:
            logger.error("无法连接到云数据库")


        for table in tables:

            # 获取表架构
            schema = self.get_table_schema(table)
            if not schema:

            # 获取表数据
            data = self.get_table_data(table)
            if not data:
                logger.info(f"表 {table} 没有数据，跳过")
                continue

            # 构建CREATE TABLE语句
            create_table_sql = self._build_create_table_sql(table, schema)
            if not create_table_sql:
                continue

            try:
                # 创建表（如果不存在）
                cloud_cursor.execute(create_table_sql)
                logger.info(f"在云数据库中创建表 {table} 成功")

                # 构建INSERT语句
                insert_sql = self._build_insert_sql(table, len(schema))
                if insert_sql:
                    # 批量插入数据
                    cloud_cursor.executemany(insert_sql, data)
                    cloud_conn.commit()
                    logger.info(f"成功迁移表 {table} 的 {len(data)} 行数据")

            except Exception as e:
                logger.error(f"迁移表 {table} 失败: {e}")
                cloud_conn.rollback()
                continue

        # 关闭连接
        cloud_conn.close()

        logger.info("数据迁移完成")
        return True

    def _build_create_table_sql(self, table_name, schema):
        """根据SQLite架构构建云数据库的CREATE TABLE语句"""
        if not schema:
            return None


        type_mapping = {
            'INTEGER': 'INT' if db_type == 'mysql' else 'INTEGER',
            'TEXT': 'VARCHAR(255)' if db_type == 'mysql' else 'TEXT',
            'REAL': 'DOUBLE' if db_type == 'mysql' else 'REAL',
            'BOOLEAN': 'TINYINT(1)' if db_type == 'mysql' else 'BOOLEAN'
        }
        columns = []
        primary_keys = []

        for col in schema:
            col_name = col[1]
            col_type = col[2]
            is_not_null = 'NOT NULL' if col[3] else ''
            is_pk = col[5]

            # 映射类型
            mapped_type = type_mapping.get(col_type, col_type)

            # 处理主键
            if is_pk:
                primary_keys.append(col_name)
            column_def = f"{col_name} {mapped_type} {is_not_null} {default_val}"
            columns.append(column_def.strip())

        # 添加主键约束
        if primary_keys:
            primary_key_clause = f", PRIMARY KEY ({', '.join(primary_keys)})"
        else:
            primary_key_clause = ""

        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)}{primary_key_clause})"
        return create_table_sql

    def _build_insert_sql(self, table_name, column_count):
        """构建INSERT语句"""
        placeholders = ', '.join(['%s'] * column_count) if self.cloud_config['database_type'] == 'mysql' else ', '.join(['%s'] * column_count)
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        return insert_sql

    def update_app_config(self):
        """更新应用程序配置以使用云数据库"""
        try:
            # 读取当前app/__init__.py文件
            with open(os.path.join('app', '__init__.py'), 'r') as f:
                content = f.read()

            cloud_uri = self.generate_cloud_db_uri()
            if not cloud_uri:
                logger.error("无法生成云数据库URI")
                return False

            # 更新数据库配置
            new_content = content

            # 替换SQLALCHEMY_DATABASE_URI
            if 'SQLALCHEMY_DATABASE_URI' in content:
                new_content = new_content.replace(
                    "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'",
                    f"app.config['SQLALCHEMY_DATABASE_URI'] = '{cloud_uri}'"
            else:
                # 如果不存在，添加配置
                new_content += f"\napp.config['SQLALCHEMY_DATABASE_URI'] = '{cloud_uri}'"

            with open(os.path.join('app', '__init__.py'), 'w') as f:
                f.write(new_content)

            logger.info("应用程序配置已更新为使用云数据库")
            return True
        except Exception as e:
            logger.error(f"更新应用程序配置失败: {e}")
            return False

    def run_full_migration(self):
        """执行完整的迁移流程"""
        logger.info("=== 开始AI脑库数据云端化迁移 ===")

        # 1. 迁移数据
        if not self.migrate_data():
            logger.error("数据迁移失败")

        # 2. 更新应用配置
        if not self.update_app_config():
            logger.error("更新应用配置失败")
            return False

        logger.info("=== AI脑库数据云端化迁移完成 ===")
        return True

if __name__ == "__main__":
    # 测试迁移功能
    cloud_db_config = CloudDatabaseConfig()
    cloud_db_config.run_full_migration()
