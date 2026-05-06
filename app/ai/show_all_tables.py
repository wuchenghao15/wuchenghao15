# -*- coding: utf-8 -*-
import os
import sqlite3
import logging

# 配置日志
logs_dir = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'show_all_tables.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ShowAllTables:
    """显示所有表内容的类"""

    def __init__(self):
        """初始化"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')

        logger.info("显示所有表内容初始化完成")

    def get_all_tables(self):
        """获取所有表名"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 查询所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            conn.close()

            # 提取表名
            table_names = [table[0] for table in tables]
            logger.info(f"发现 {len(table_names)} 个表")
            return table_names
        except Exception as e:
            logger.error(f"获取表名失败: {str(e)}")
            return []

    def show_table_content(self, table_name):
        """显示表内容"""
            conn = sqlite3.connect(self.db_path)

            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]

            # 查询表内容
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            conn.close()

            logger.info(f"表 {table_name} 有 {len(rows)} 行数据")
        except Exception as e:
            logger.error(f"显示表 {table_name} 内容失败: {str(e)}")
            return [], []

        """运行显示所有表内容"""
            logger.info("开始显示所有表内容")

            # 获取所有表名
            table_names = self.get_all_tables()

            # 显示每个表的内容
            for table_name in table_names:
                logger.info(f"\n=== 表: {table_name} ===")

                # 显示表内容
                column_names, rows = self.show_table_content(table_name)

                if column_names:
                    # 显示列名
                    logger.info(f"列名: {', '.join(column_names)}")

                    # 显示数据
                    if rows:
                        logger.info("数据:")
                        for row in rows:
                            logger.info(row)
                    else:
                        logger.info("该表为空")
                else:
                    logger.info("无法获取表结构")

            logger.info("显示所有表内容完成")
        except Exception as e:
            logger.error(f"运行显示所有表内容失败: {str(e)}")
if __name__ == "__main__":
    show_tables = ShowAllTables()
