#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - 系统初始化脚本
执行系统初始化、依赖检查、数据库初始化等操作
"""

import os
import sys
import subprocess
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        logger.error(
        f"Python版本需要3.8或更高，当前版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return False
    logger.info(f"Python版本检查通过: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_dependencies():
    """检查依赖是否安装"""
    required_modules = [
        'flask', 'flask_cors', 'werkzeug', 'requests', 'pyyaml', 'psutil', 'schedule', 'numpy'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✓ 依赖模块: {module}")
        except ImportError:
            missing.append(module)
            logger.warning(f"✗ 缺少依赖: {module}")
    
    if missing:
        logger.error(f"缺少 {len(missing)} 个依赖模块")
        return False
    logger.info("所有依赖检查通过")
    return True


def install_dependencies():
    """安装依赖"""
    logger.info("开始安装依赖...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        if result.returncode == 0:
            logger.info("依赖安装成功")
            return True
        else:
            logger.error(f"依赖安装失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"依赖安装异常: {str(e)}")
        return False


def init_database():
    """初始化数据库表结构"""
    db_path = os.path.join(BASE_DIR, 'app.db')
    logger.info(f"初始化数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建必要的表
        tables = [
            '''CREATE TABLE IF NOT EXISTS version_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                build_number INTEGER,
                build_date TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT NOT NULL,
                value TEXT,
                category TEXT DEFAULT 'general',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT DEFAULT 'INFO',
                module TEXT,
                message TEXT,
                ip_address TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                super_admin_approved INTEGER DEFAULT 0,
                hardware_admin_approved INTEGER DEFAULT 0,
                avatar TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS exam_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                exam_id INTEGER,
                status TEXT DEFAULT 'in_progress',
                score REAL DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                language TEXT DEFAULT 'zh',
                level TEXT DEFAULT 'intermediate',
                duration INTEGER DEFAULT 60,
                question_count INTEGER DEFAULT 20,
                total_points REAL DEFAULT 100.0,
                passing_score REAL DEFAULT 60.0,
                status TEXT DEFAULT 'draft',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER,
                question_text TEXT,
                type TEXT DEFAULT 'choice',
                options TEXT,
                answer TEXT,
                difficulty TEXT DEFAULT 'medium',
                subject TEXT,
                category TEXT,
                tags TEXT,
                points REAL DEFAULT 5.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        # 检查是否需要初始化默认数据
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            cursor.execute(
                'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                ('admin', generate_password_hash('admin123'), 'admin@example.com', 'super_admin')
            )
            logger.info("创建默认管理员用户: admin/admin123")
        
        # 检查版本记录
        cursor.execute('SELECT COUNT(*) FROM version_control')
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                'INSERT INTO version_control (version, build_number, build_date, description) VALUES (?, ?, ?, ?)',
                ('3.1.0', 5679, datetime.now().isoformat(), '系统初始化')
            )
            logger.info("记录初始版本: 3.1.0")
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False


def init_directories():
    """初始化目录结构"""
    dirs_to_create = [
        'uploads',
        'cache/l2',
        'cache/l3',
        'ssl',
        'logs',
        'databases',
    ]
    
    for dir_path in dirs_to_create:
        full_path = os.path.join(BASE_DIR, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"创建目录: {dir_path}")
        else:
            logger.debug(f"目录已存在: {dir_path}")
    
    logger.info("目录结构初始化完成")
    return True


def init_database_config():
    """初始化数据库配置（将系统参数写入数据库）"""
    logger.info("初始化数据库配置...")
    try:
        from app.config import init_database_config
        init_database_config()
        logger.info("数据库配置初始化完成")
        return True
    except Exception as e:
        logger.error(f"数据库配置初始化失败: {str(e)}")
        return False


def run_tests():
    """运行系统测试"""
    logger.info("开始运行系统测试...")
    try:
        result = subprocess.run(
            [sys.executable, '-c', '''
import sys
sys.path.insert(0, ".")
from app import app

tests_pass = 0
tests_fail = 0

with app.test_client() as client:
    # 测试健康检查
    resp = client.get("/api/health")
    tests_pass += 1 if resp.status_code == 200 else 0
    tests_fail += 1 if resp.status_code != 200 else 0
    
    # 测试系统状态(使用/api/status)
    resp = client.get("/api/status")
    tests_pass += 1 if resp.status_code == 200 else 0
    tests_fail += 1 if resp.status_code != 200 else 0
    
    # 测试握手
    resp = client.get("/api/handshake")
    tests_pass += 1 if resp.status_code == 200 else 0
    tests_fail += 1 if resp.status_code != 200 else 0
    
    # 测试心跳
    resp = client.get("/api/heartbeat")
    tests_pass += 1 if resp.status_code == 200 else 0
    tests_fail += 1 if resp.status_code != 200 else 0
    
    # 测试版本信息
    resp = client.get("/api/version/version")
    tests_pass += 1 if resp.status_code == 200 else 0
    tests_fail += 1 if resp.status_code != 200 else 0
    
    print(f"测试完成: 通过={tests_pass}, 失败={tests_fail}")
'''],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        if result.returncode == 0:
            logger.info(f"系统测试完成")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"测试失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"测试执行异常: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("MTSCOS AI Project - 系统初始化")
    logger.info("=" * 60)
    logger.info(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"版本: 3.1.0")
    logger.info(f"项目目录: {BASE_DIR}")
    logger.info("=" * 60)
    
    # 步骤1: 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 步骤2: 检查依赖
    if not check_dependencies():
        logger.info("尝试安装缺失的依赖...")
        if not install_dependencies():
            sys.exit(1)
    
    # 步骤3: 初始化目录结构
    init_directories()
    
    # 步骤4: 初始化数据库
    init_database()
    
    # 步骤5: 初始化数据库配置
    init_database_config()
    
    # 步骤6: 运行系统测试
    run_tests()
    
    logger.info("=" * 60)
    logger.info("系统初始化完成!")
    logger.info("=" * 60)
    logger.info("启动命令: python3 app.py")
    logger.info("访问地址: http://localhost:8443")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
