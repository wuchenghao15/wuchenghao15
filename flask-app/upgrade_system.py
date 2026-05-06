#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统升级和优化脚本
更新系统版本，优化配置，清理垃圾文件

import os
# JSON import removed - using database
import logging
import time
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'upgrade_system_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('upgrade_system')

# 系统版本信息
CURRENT_VERSION = "1.0.0"
NEW_VERSION = "2.0.0"

def check_system_status():
    """检查系统状态"""
    logger.info("开始检查系统状态...")

    # 检查系统文件结构
    required_dirs = [
        'app', 'app/ai', 'app/blueprints', 'app/config', 'app/services',
        'app/utils', 'data', 'logs', 'static', 'templates'
    ]
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            logger.info(f"✅ 目录存在: {dir_path}")
        else:
            logger.warning(f"❌ 目录缺失: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"📁 创建目录: {dir_path}")

    # 检查关键文件
    required_files = [
        'app/__init__.py', 'app.py', 'system_init.py',
        'app/config/ai_engine_config.json', 'app/config/system_config.json'
    ]
    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"✅ 文件存在: {file_path}")
        else:
            logger.warning(f"❌ 文件缺失: {file_path}")


def update_system_version():
    """更新系统版本"""
    logger.info(f"开始更新系统版本: {CURRENT_VERSION} → {NEW_VERSION}")

    # 更新系统配置文件
    system_config = {
        "version": NEW_VERSION,
        "last_updated": datetime.now().isoformat(),
        "system": {
            "name": "MTSCOS AI Project",
            "description": "AI-powered educational system",
            "author": "MTSCOS Team",
            "release_date": datetime.now().isoformat(),
            "status": "production"
        },
        "features": [
            "AI-powered learning",
            "Intelligent exam system",
            "Real-time monitoring",
            "Automated testing",
            "Security scanning",
            "Performance optimization"
        ],
        "dependencies": {
            "python": "3.8+",
            "flask": "2.0+",
            "sqlite3": "3.30+",
            "requests": "2.25+"
        }
    }

    config_dir = 'app/config'
    if not os.path.exists(config_dir):

    system_config_file = os.path.join(config_dir, 'system_config.json')
    with open(system_config_file, 'w', encoding='utf-8') as f:
        json.dump(system_config, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 更新系统配置文件: {system_config_file}")

    # 创建版本信息文件
    version_info = {
        "current_version": NEW_VERSION,
        "previous_version": CURRENT_VERSION,
        "update_date": datetime.now().isoformat(),
        "update_notes": [
            "系统核心组件升级",
            "AI引擎配置优化",
            "性能监控增强",
            "安全功能提升",
            "用户体验改进"
        ]

    version_file = os.path.join(config_dir, 'version_info.json')
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 创建版本信息文件: {version_file}")

    logger.info(f"系统版本更新完成: {NEW_VERSION}")

def optimize_system_config():
    """优化系统配置"""
    logger.info("开始优化系统配置...")

    # 优化Flask配置
    flask_config = {
        "DEBUG": False,
        "SECRET_KEY": "your-secret-key-here",
        "PERMANENT_SESSION_LIFETIME": 86400,
        "SESSION_TYPE": "filesystem",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///data/mtscos_ai_project.db",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JSON_SORT_KEYS": False,
        "JSONIFY_MIMETYPE": "application/json; charset=utf-8",
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,  # 16MB
        "TEMPLATES_AUTO_RELOAD": True
    }

    config_dir = 'app/config'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    flask_config_file = os.path.join(config_dir, 'flask_config.json')
    with open(flask_config_file, 'w', encoding='utf-8') as f:
        json.dump(flask_config, f, ensure_ascii=False, indent=2)


    performance_config = {
        "last_updated": datetime.now().isoformat(),
        "performance": {
            "cache": {
                "enabled": True,
                "cache_timeout": 3600,
            },
            "thread_pool": {
                "size": 8,
                "max_workers": 16
            },
            "request": {
                "timeout": 30,
                "rate_limit": 600
            },
            "database": {
                "max_overflow": 10,
                "pool_timeout": 30
            }
        }

    performance_config_file = os.path.join(config_dir, 'performance_config.json')
    with open(performance_config_file, 'w', encoding='utf-8') as f:
        json.dump(performance_config, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 优化性能配置: {performance_config_file}")

    """清理系统垃圾文件"""
    logger.info("开始清理系统垃圾文件...")

    # 清理临时文件
    temp_dirs = ['temp', 'cache', 'logs']
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            try:
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isfile(item_path):
                        # 只删除7天前的文件
                        file_mtime = os.path.getmtime(item_path)
                        if time.time() - file_mtime > 7 * 24 * 3600:
                            os.remove(item_path)
                            logger.info(f"🗑️ 清理过期文件: {item_path}")
            except Exception as e:
                logger.error(f"清理临时文件失败: {str(e)}")

    # 清理Python缓存文件
    pycache_dirs = []
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                pycache_dirs.append(os.path.join(root, dir_name))

    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            logger.info(f"🗑️ 清理Python缓存: {pycache_dir}")
        except Exception as e:
            logger.error(f"清理Python缓存失败: {str(e)}")

    # 清理编译的Python文件
    pyc_files = []
    for root, dirs, files in os.walk('.'):
        for file_name in files:
            if file_name.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file_name))

    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            logger.info(f"🗑️ 清理编译文件: {pyc_file}")
        except Exception as e:
            logger.error(f"清理编译文件失败: {str(e)}")
    logger.info("系统垃圾文件清理完成")

def update_dependencies():
    """更新依赖项"""
    logger.info("开始更新依赖项...")

    # 创建/更新requirements.txt文件
    requirements = [
        "Flask-SQLAlchemy==2.5.1",
        "Flask-Login==0.5.0",
        "Flask-Session==0.4.0",
        "requests==2.26.0",
        "python-dotenv==0.19.0",
        "psutil==5.8.0",
        "gunicorn==20.1.0"
    ]
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(requirements))

    logger.info("✅ 更新依赖配置文件: requirements.txt")

    # 尝试安装依赖
    try:
        import subprocess
        result = subprocess.run(
            ['pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("✅ 依赖安装成功")
        else:
            logger.warning("⚠️ 依赖安装可能存在问题，请手动检查")
            logger.debug(f"依赖安装错误: {result.stderr}")
    except Exception as e:
        logger.error(f"更新依赖失败: {str(e)}")
    logger.info("依赖项更新完成")

def optimize_database():
    """优化数据库"""
    logger.info("开始优化数据库...")

    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 检查数据库文件
    db_file = os.path.join(data_dir, 'mtscos_ai_project.db')
    if os.path.exists(db_file):
        logger.info(f"✅ 数据库文件存在: {db_file}")

        # 尝试优化数据库
        try:
            import sqlite3
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # 运行VACUUM命令优化数据库
            cursor.execute('VACUUM')
            conn.commit()

            # 分析数据库
            cursor.execute('ANALYZE')
            conn.commit()

            conn.close()
            logger.info("✅ 数据库优化完成")
        except Exception as e:
            logger.error(f"数据库优化失败: {str(e)}")
    else:
        logger.warning(f"⚠️ 数据库文件不存在: {db_file}")
        logger.info("系统启动时会自动创建数据库")

    logger.info("数据库优化完成")
    """验证升级结果"""
    logger.info("开始验证升级结果...")

    # 验证版本信息
    version_file = os.path.join('app/config', 'version_info.json')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            version_info = json.load(f)
        logger.info(f"✅ 版本信息: {version_info['current_version']}")
        logger.info(f"✅ 上一版本: {version_info['previous_version']}")
        logger.info(f"✅ 更新日期: {version_info['update_date']}")
    else:
        logger.warning("⚠️ 版本信息文件不存在")

    # 验证系统配置
    if os.path.exists(system_config_file):
            system_config = json.load(f)
        logger.info(f"✅ 系统版本: {system_config.get('version')}")
        logger.info(f"✅ 系统名称: {system_config.get('system', {}).get('name')}")
    else:
        logger.warning("⚠️ 系统配置文件不存在")

    # 验证目录结构
    required_dirs = ['app', 'data', 'logs']
    for dir_path in required_dirs:
            logger.info(f"✅ 关键目录存在: {dir_path}")
        else:
            logger.error(f"❌ 关键目录缺失: {dir_path}")

    required_files = ['app.py', 'system_init.py']
        if os.path.exists(file_path):
            logger.info(f"✅ 关键文件存在: {file_path}")
            logger.error(f"❌ 关键文件缺失: {file_path}")

    logger.info("升级验证完成")

def main():
    """主函数"""
    logger.info("=== 开始系统升级和优化 ===")
    try:
        # 1. 检查系统状态
        check_system_status()
        # 2. 更新系统版本

        # 3. 优化系统配置
        optimize_system_config()

        # 4. 清理系统垃圾文件
        cleanup_system()

        # 5. 更新依赖项
        update_dependencies()

        # 6. 优化数据库
        optimize_database()

        # 7. 验证升级结果
        verify_upgrade()

        logger.info("=== 系统升级和优化完成 ===")
        logger.info(f"系统已成功升级到版本 {NEW_VERSION}")
        logger.info("系统优化已完成，性能和安全性得到提升")

    except Exception as e:
        logger.error(f"升级过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

    main()
