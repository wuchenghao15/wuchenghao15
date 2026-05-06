#!/usr/bin/env python3
"""
AI脑库数据云端化配置脚本

import os
import sys
# JSON import removed - using database
import sqlite3
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud_database_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cloud_database_config')

class CloudDatabaseConfig:
    云端数据库配置和迁移管理

    def __init__(self):
        初始化云端数据库配置
        self.config_file = 'config/cloud_database.conf'
        self.local_db_path = 'app.db'
        self.cloud_config = self.load_cloud_config()

    def load_cloud_config(self):
        加载云端数据库配置
        if not os.path.exists(self.config_file):
            logger.error(f"云端配置文件不存在: {self.config_file}")
            return None

        config = {}
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

        logger.info(f"加载云端配置成功: {config}")
        return config

    def generate_cloud_db_uri(self, database_type='mysql'):
        生成云端数据库连接URI
        if not self.cloud_config:

        if database_type == 'mysql':
            return f"mysql+pymysql://{self.cloud_config['DB_USER']}:{self.cloud_config['DB_PASSWORD']}@{self.cloud_config['DB_HOST']}:{self.cloud_config['DB_PORT']}/{self.cloud_config['DB_NAME']}?charset=utf8mb4"
        elif database_type == 'postgresql':
            return f"postgresql://{self.cloud_config['DB_USER']}:{self.cloud_config['DB_PASSWORD']}@{self.cloud_config['DB_HOST']}:{self.cloud_config['DB_PORT']}/{self.cloud_config['DB_NAME']}?client_encoding=utf8"
        else:
            logger.error(f"不支持的数据库类型: {database_type}")
    def update_config_file(self):
        更新配置文件，将数据库连接改为云端数据库
        # 更新flask-app/app/config.py中的数据库配置
        config_file = 'flask-app/app/config.py'
        if not os.path.exists(config_file):
            logger.error(f"配置文件不存在: {config_file}")
            return False
        with open(config_file, 'r') as f:
            content = f.read()

        # 生成云端数据库连接URI
        cloud_uri = self.generate_cloud_db_uri()
        if not cloud_uri:
            return False

        updated_content = content

        # 更新基础配置
        updated_content = updated_content.replace(
            'SQLALCHEMY_DATABASE_URI = os.environ.get(\'DATABASE_URL\') or f\'sqlite:///{DATABASE_PATH}\'',
            f'SQLALCHEMY_DATABASE_URI = os.environ.get(\'DATABASE_URL\') or \'{cloud_uri}\''

        # 更新开发环境配置
        updated_content = updated_content.replace(
            'SQLALCHEMY_DATABASE_URI = os.environ.get(\'DATABASE_URL\') or f\'sqlite:///{DATABASE_PATH}\'',
            f'SQLALCHEMY_DATABASE_URI = os.environ.get(\'DATABASE_URL\') or \'{cloud_uri}\''

        with open(config_file, 'w') as f:
        logger.info(f"更新配置文件成功: {config_file}")

    def check_cloud_connection(self):
        检查云端数据库连接
            return False
        try:
            from sqlalchemy import create_engine
            engine = create_engine(cloud_uri)
            connection.close()
            logger.info("云端数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"云端数据库连接失败: {str(e)}")
            return False

    def get_local_tables(self):
        if not os.path.exists(self.local_db_path):

        conn = sqlite3.connect(self.local_db_path)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        conn.close()

        logger.info(f"本地数据库表: {tables}")
        return tables

    def migrate_data(self):
        将本地数据迁移到云端数据库
        if not self.check_cloud_connection():
            logger.error("云端数据库连接失败，无法迁移数据")
            return False

        # 获取本地表
        tables = self.get_local_tables()
            logger.error("本地数据库中没有表，无需迁移")
            return True

        logger.info(f"开始迁移 {len(tables)} 个表到云端数据库")

        try:
            # 连接本地数据库
            local_conn = sqlite3.connect(self.local_db_path)
            local_cursor = local_conn.cursor()

            # 连接云端数据库
            from sqlalchemy import create_engine, MetaData, Table
            engine = create_engine(cloud_uri)
            cloud_conn = engine.connect()
            metadata = MetaData()
            metadata.reflect(bind=engine)

            for table_name in tables:

                # 获取表结构
                local_cursor.execute(f"PRAGMA table_info({table_name});")
                columns = local_cursor.fetchall()

                # 获取表数据
                local_cursor.execute(f"SELECT * FROM {table_name};")

                if not rows:
                    continue
                # 检查云端是否已有该表
                if table_name in metadata.tables:
                    table = metadata.tables[table_name]

                    # 清空表数据
                    cloud_conn.execute(table.delete())

                    for row in rows:
                        # 将行转换为字典
                        row_dict = {}
                        for i, col in enumerate(columns):
                            row_dict[col[1]] = row[i]

                        # 插入数据
                        cloud_conn.execute(table.insert().values(**row_dict))

                    logger.info(f"成功迁移表 {table_name}，共 {len(rows)} 条记录")
                else:
                    logger.error(f"云端数据库中不存在表 {table_name}，跳过迁移")

            # 提交事务

            # 关闭连接
            local_conn.close()
            cloud_conn.close()

            logger.info("数据迁移完成")
            return True
        except Exception as e:
            logger.error(f"数据迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def update_env_file(self):
        更新环境变量文件，添加云端数据库配置
        env_file = '.env'
        env_content = f"# 云端数据库配置\n"
        env_content += f"DATABASE_URL={self.generate_cloud_db_uri()}\n"
        env_content += f"DB_HOST={self.cloud_config['DB_HOST']}\n"
        env_content += f"DB_USER={self.cloud_config['DB_USER']}\n"
        env_content += f"DB_PASSWORD={self.cloud_config['DB_PASSWORD']}\n"

        # 写入环境变量文件
        with open(env_file, 'w') as f:

        logger.info(f"环境变量文件更新成功: {env_file}")
        return True

    def run_full_migration(self):
        执行完整的迁移流程
        logger.info("开始执行完整的云端迁移流程")

        if not self.cloud_config:
            logger.error("云端配置加载失败")
            return False

        if not self.check_cloud_connection():
            logger.error("云端数据库连接失败")
            return False
        # 3. 更新配置文件
            logger.error("配置文件更新失败")
            return False
        # 4. 更新环境变量文件
        if not self.update_env_file():
            logger.error("环境变量文件更新失败")
            return False
        # 5. 迁移数据
        if not self.migrate_data():
            logger.error("数据迁移失败")
            return False
        logger.info("完整迁移流程执行成功")

if __name__ == '__main__':
    config = CloudDatabaseConfig()

"""