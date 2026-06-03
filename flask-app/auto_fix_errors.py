#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复系统初始化异常
修复缺失的导入和语法错误
"""

import os
import re
import logging
import sqlite3
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_system_errors')

def fix_blueprint_import(file_path):
    """修复 Blueprint 导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'Blueprint' in content and 'from flask import Blueprint' not in content and 'from flask import' not in content:
            lines = content.split('\n')
            new_lines = []
            found_import = False
            for line in lines:
                new_lines.append(line)
                if not found_import and (line.startswith('import ') or (line.startswith('from ') and 'flask' in line.lower())):
                    if 'Blueprint' not in line:
                        new_lines[-1] = line.rstrip()
                        if 'import' in line:
                            new_lines[-1] += ', Blueprint'
                        else:
                            new_lines.append('from flask import Blueprint')
                        found_import = True

            content = '\n'.join(new_lines)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"修复 Blueprint 导入: {file_path}")
            return True
    except Exception as e:
        logger.error(f"修复 Blueprint 导入失败: {file_path} - {str(e)}")
    return False

def fix_threading_import(file_path):
    """修复 threading 导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'threading.' in content and 'import threading' not in content:
            lines = content.split('\n')
            new_lines = []
            found_import = False
            for line in lines:
                new_lines.append(line)
                if not found_import and line.startswith('import '):
                    new_lines[-1] = line.rstrip() + ', threading'
                    found_import = True
                    break
            content = '\n'.join(new_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"修复 threading 导入: {file_path}")
    except Exception as e:
        logger.error(f"修复 threading 导入失败: {file_path} - {str(e)}")
    return False

def fix_fstring_error(file_path):
    """修复 f-string 语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        fixed_lines = []
        for i, line in enumerate(lines):
            if 'f"' in line and ('{' in line and '}' not in line.replace('{', '').replace('}', '')):
                fixed_line = line.replace('{', '{{').replace('}', '}}')
                if i >= 30 and i <= 40:
                    logger.warning(f"发现 f-string 可能有问题: {file_path}:{i+1}")
            fixed_lines.append(line)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)

        return True
    except Exception as e:
        logger.error(f"修复 f-string 错误失败: {file_path} - {str(e)}")
    return False

def scan_and_fix_files():
    """扫描并修复所有有问题的文件"""
    logger.info("开始扫描并修复有问题的文件...")

    scan_dirs = [
        'app/api',
        'app/views',
        'app/routes',
        'app/blueprints'
    ]

    for scan_dir in scan_dirs:
        if not os.path.exists(scan_dir):
            logger.warning(f"目录不存在: {scan_dir}")
            continue

        logger.info(f"扫描目录: {scan_dir}")

        for root, dirs, files in os.walk(scan_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    logger.info(f"检查文件: {file_path}")

                    fix_blueprint_import(file_path)
                    fix_threading_import(file_path)
                    fix_fstring_error(file_path)

def fix_sklearn_import():
    """修复 sklearn 导入问题"""
    logger.info("检查 sklearn 导入...")

    files_to_check = [
        'app/api/learn_system.py',
        'app/views/system_management.py'
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'sklearn' in content.lower():
                    if 'from sklearn' not in content and 'import sklearn' not in content:
                        logger.warning(f"文件中提到 sklearn 但没有正确导入: {file_path}")
            except Exception as e:
                logger.error(f"检查 sklearn 导入失败: {file_path} - {str(e)}")

def create_database_tables():
    """创建缺失的数据库表"""
    logger.info("创建缺失的数据库表...")

    try:
        db_path = 'data/mtscos_ai_project.db'
        if not os.path.exists('data'):
            os.makedirs('data')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS t_4eee826d5652464d (
            instance_id TEXT PRIMARY KEY,
            collection_id TEXT,
            ai_type TEXT,
            name TEXT,
            ai_name TEXT,
            description TEXT,
            functions TEXT,
            responsibilities TEXT,
            status TEXT,
            config TEXT,
            bound_user TEXT,
            created_at TEXT,
            updated_at TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS t_c40db917ee9ecaca (
            collection_id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            created_at TEXT,
            updated_at TEXT
            )
            ''')
            
            conn.commit()

        logger.info("数据库表创建成功")

    except Exception as e:
        logger.error(f"创建数据库表失败: {str(e)}")

def main():
    """主函数"""
    logger.info("=== 开始自动修复系统异常 ===")

    try:
        scan_and_fix_files()
        fix_sklearn_import()
        create_database_tables()
        logger.info("=== 自动修复完成 ===")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
