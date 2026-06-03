# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sqlite3
import os
import argparse
import glob
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class JsonToDbUploader:
    def __init__(self, db_path, table_name):
        self.db_path = db_path
        self.table_name = table_name
        self.conn = None
        self.cursor = None
        self.uploaded_count = 0
        self.deleted_count = 0
        self.error_count = 0
        
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"成功连接到数据库: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
            
    def disconnect(self):
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")
            
    def create_table(self, data):
        if not data or not isinstance(data, list):
            logger.error("数据格式错误，需要是列表格式")
            return False
            
        if len(data) == 0:
            logger.error("数据为空")
            return False
            
        first_item = data[0]
        columns = []
        for key, value in first_item.items():
            col_type = self.get_sql_type(value)
            columns.append(f"{key} {col_type}")
            
        create_sql = f"CREATE TABLE IF NOT EXISTS {self.table_name} ({', '.join(columns)})"
        try:
            self.cursor.execute(create_sql)
            self.conn.commit()
            logger.info(f"表 {self.table_name} 创建成功")
            return True
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            return False
            
    def get_sql_type(self, value):
        if isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "REAL"
        elif isinstance(value, bool):
            return "INTEGER"
        elif isinstance(value, (list, dict)):
            return "TEXT"
        else:
            return "TEXT"
            
    def insert_data(self, data):
        if not data or not isinstance(data, list):
            logger.error("数据格式错误")
            return False
            
        for item in data:
            try:
                keys = list(item.keys())
                placeholders = ','.join(['?' for _ in keys])
                values = []
                for key in keys:
                    val = item.get(key)
                    if isinstance(val, (list, dict)):
                        val = json.dumps(val, ensure_ascii=False)
                    values.append(val)
                insert_sql = f"INSERT INTO {self.table_name} ({','.join(keys)}) VALUES ({placeholders})"
                self.cursor.execute(insert_sql, values)
                self.uploaded_count += 1
            except Exception as e:
                logger.error(f"插入数据失败: {e}")
                self.error_count += 1
                
        self.conn.commit()
        return True
        
    def upload_file(self, json_file):
        logger.info(f"开始上传文件: {json_file}")
        
        if not os.path.exists(json_file):
            logger.error(f"文件不存在: {json_file}")
            return False
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                data = [data]
                
            if not self.connect():
                return False
                
            if not self.create_table(data):
                self.disconnect()
                return False
                
            if not self.insert_data(data):
                self.disconnect()
                return False
                
            self.disconnect()
            logger.info(f"文件 {json_file} 上传成功，共 {len(data)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            if self.conn:
                self.disconnect()
            return False
            
    def delete_file(self, json_file):
        try:
            os.remove(json_file)
            self.deleted_count += 1
            logger.info(f"已删除文件: {json_file}")
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
            
    def upload_and_delete(self, json_file):
        if self.upload_file(json_file):
            self.delete_file(json_file)
            return True
        return False
        
    def batch_upload(self, json_dir, delete_after=False):
        json_files = glob.glob(os.path.join(json_dir, '*.json'))
        logger.info(f"找到 {len(json_files)} 个JSON文件")
        
        for json_file in json_files:
            logger.info(f"处理文件: {json_file}")
            if self.upload_file(json_file):
                if delete_after:
                    self.delete_file(json_file)
        
        logger.info(f"批量上传完成，上传: {self.uploaded_count} 条记录，删除: {self.deleted_count} 个文件，错误: {self.error_count}")
        
    def get_upload_stats(self):
        return {
            'uploaded_count': self.uploaded_count,
            'deleted_count': self.deleted_count,
            'error_count': self.error_count
        }

def main():
    parser = argparse.ArgumentParser(description='JSON数据上传工具')
    parser.add_argument('--file', help='单个JSON文件路径')
    parser.add_argument('--dir', help='JSON文件目录')
    parser.add_argument('--table', required=True, help='目标表名')
    parser.add_argument('--db', required=True, help='数据库路径')
    parser.add_argument('--delete', action='store_true', help='上传后删除文件')
    
    args = parser.parse_args()
    
    uploader = JsonToDbUploader(args.db, args.table)
    
    if args.file:
        if uploader.upload_file(args.file):
            if args.delete:
                uploader.delete_file(args.file)
            print(f"上传成功！")
        else:
            print(f"上传失败！")
            
    elif args.dir:
        uploader.batch_upload(args.dir, args.delete)
        stats = uploader.get_upload_stats()
        print(f"批量上传完成！上传: {stats['uploaded_count']} 条记录，删除: {stats['deleted_count']} 个文件")
        
    else:
        print("请指定 --file 或 --dir 参数")

if __name__ == '__main__':
    main()
