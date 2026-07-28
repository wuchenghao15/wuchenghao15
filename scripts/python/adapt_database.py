#!/usr/bin/env python3
import os
import re

APP_PY_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.py'

def add_db_manager_import(content):
    import_section = """from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file,
    send_from_directory, abort, session, make_response
import os
import sys
import json
import sqlite3"""
    
    new_import_section = """from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,
    send_file, send_from_directory, abort, session, make_response
import os
import sys
import json
import sqlite3
from db_manager import connect, get_db_for_table, TABLE_TO_DB"""
    
    return content.replace(import_section, new_import_section)

def create_smart_connect_function():
    return """
def get_db_connection(table_name=None):
    if table_name:
        db_name = get_db_for_table(table_name)
        return connect(db_name)
    return sqlite3.connect(DATABASE_PATH_LEGACY)

class SmartDatabase:
    def connect(self, path):
        return sqlite3.connect(path)

smart_db = SmartDatabase()
"""

def adapt_database():
    with open(APP_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = add_db_manager_import(content)
    
    content = content.replace(
        "DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')",
        "DATABASE_PATH_LEGACY = os.path.join(os.path.dirname(os.path.abspath(__file__)),'app.db')\nDATABASE_PATH = 'smart://distributed'"
    )
    
    db_helper_code = """
class DistributedDBHelper:
    def __init__(self):
        from db_manager import connect, get_db_for_table, TABLE_TO_DB, build_table_mapping
        self.connect = connect
        self.get_db_for_table = get_db_for_table
        self.TABLE_TO_DB = TABLE_TO_DB
        build_table_mapping()
    
    def get_connection(self, table_name):
        db_name = self.get_db_for_table(table_name)
        return self.connect(db_name)

db_helper = DistributedDBHelper()

def smart_connect(table_name):
    return db_helper.get_connection(table_name)
"""
    
    insert_after = "DATABASE_PATH = 'smart://distributed'"
    content = content.replace(insert_after, insert_after + db_helper_code)
    
    logger.info("已添加db_manager导入和智能连接函数")
    
    with open(APP_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("app.py已更新")

if __name__ == "__main__":
    adapt_database()
    logger.info("\n适配完成！")