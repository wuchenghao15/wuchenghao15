#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - 自动化初始化脚本

这个脚本提供了项目的统一自动化初始化流程，包括：
1. 环境检查
2. 依赖安装
3. 数据库初始化
4. 目录结构创建
5. AI系统初始化
6. 应用启动

用法：
    python3 automated_setup.py [--skip-deps] [--skip-db] [--skip-ai] [--start-app]

选项：
    --skip-deps       跳过依赖安装
    --skip-db         跳过数据库初始化
    --skip-ai         跳过AI系统初始化
    --start-app       初始化完成后启动应用
    --help            显示帮助信息
"""

import os
import sys
import logging
import argparse
import subprocess
import time

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('automated_setup')

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 确保项目根目录在Python路径中
sys.path.insert(0, PROJECT_ROOT)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MTSCOS AI Project - 自动化初始化脚本')
    parser.add_argument('--skip-deps', action='store_true', help='跳过依赖安装')
    parser.add_argument('--skip-db', action='store_true', help='跳过数据库初始化')
    parser.add_argument('--skip-ai', action='store_true', help='跳过AI系统初始化')
    parser.add_argument('--start-app', action='store_true', help='初始化完成后启动应用')
    return parser.parse_args()


def check_environment():
    """检查系统环境"""
    logger.info("🔍 检查系统环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 7):
        logger.error(f"❌ Python版本过低，需要3.7+，当前版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        return False
    logger.info(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查pip
    try:
        import pip
        logger.info("✅ pip已安装")
    except ImportError:
        logger.error("❌ pip未安装")
        return False
    
    # 检查项目目录结构
    required_dirs = ['app', 'static', 'templates', 'config']
    for dir_name in required_dirs:
        dir_path = os.path.join(PROJECT_ROOT, dir_name)
        if not os.path.exists(dir_path):
            logger.warning(f"⚠️ 目录不存在: {dir_path}")
            try:
                os.makedirs(dir_path)
                logger.info(f"✅ 创建目录: {dir_path}")
            except Exception as e:
                logger.error(f"❌ 创建目录失败: {dir_path}, 错误: {str(e)}")
                return False
    
    # 检查配置文件
    config_files = ['app/config.py', 'requirements.txt']
    for file_path in config_files:
        full_path = os.path.join(PROJECT_ROOT, file_path)
        if not os.path.exists(full_path):
            logger.warning(f"⚠️ 配置文件不存在: {full_path}")
    
    logger.info("✅ 环境检查完成")
    return True


def install_dependencies():
    """安装项目依赖"""
    logger.info("📦 安装项目依赖...")
    
    requirements_file = os.path.join(PROJECT_ROOT, 'requirements.txt')
    if not os.path.exists(requirements_file):
        logger.warning(f"⚠️ 依赖文件不存在: {requirements_file}")
        return True
    
    try:
        # 使用pip安装依赖
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', requirements_file, '--upgrade'],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"✅ 依赖安装成功")
        if result.stdout:
            logger.debug(f"安装输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 依赖安装失败: {e.stderr}")
        return False


def init_database():
    """初始化数据库"""
    logger.info("🗄️  初始化数据库...")
    
    try:
        # 运行现有的数据库初始化脚本
        init_script = os.path.join(PROJECT_ROOT, 'init_and_update_db.py')
        if os.path.exists(init_script):
            result = subprocess.run(
                [sys.executable, init_script],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"✅ 数据库初始化成功")
            if result.stdout:
                logger.debug(f"数据库初始化输出: {result.stdout}")
        else:
            # 如果没有现有脚本，直接创建表
            logger.info("⚠️  未找到数据库初始化脚本，直接创建表...")
            
            # 导入所有模型并创建表
            from app.models.user import User
            from app.models.system_config import SystemConfig
            from app.models.backup import Backup
            from app.models.logs import LogEntry
            from app.models.user_snapshots import UserSnapshot
            from app.models.ai import AIInstance
            from app.models.local_data import LocalData
            
            User.create_table()
            SystemConfig.create_table()
            Backup.create_table()
            LogEntry.create_table()
            UserSnapshot.create_table()
            AIInstance.create_table()
            LocalData.create_table()
            
            logger.info("✅ 所有数据库表创建成功")
            
            # 运行数据库更新脚本
            update_script = os.path.join(PROJECT_ROOT, 'update_database.py')
            if os.path.exists(update_script):
                result = subprocess.run(
                    [sys.executable, update_script],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"✅ 数据库更新成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def create_directories():
    """创建必要的目录结构"""
    logger.info("📁 创建必要的目录结构...")
    
    directories = [
        'data',
        'logs',
        'backups',
        'static/avatars',
        'static/css',
        'static/js',
        'static/js/vikey',
        'static/js/utils',
        'templates',
        'instance',
        'docs'
    ]
    
    for dir_path in directories:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
                logger.info(f"✅ 创建目录: {full_path}")
            except Exception as e:
                logger.error(f"❌ 创建目录失败: {full_path}, 错误: {str(e)}")
                return False
    
    logger.info("✅ 目录结构创建完成")
    return True


def init_ai_system():
    """初始化AI系统"""
    logger.info("🤖 初始化AI系统...")
    
    try:
        # 导入并初始化AI集
        from app.ai.ai_ensemble import AIEnsemble
        ai_ensemble = AIEnsemble()
        logger.info(f"✅ AI集初始化成功: {ai_ensemble.ensemble_id}")
        logger.info(f"   项目功能: {ai_ensemble.project_features}")
        logger.info(f"   所需AI类型: {ai_ensemble.required_ai_types}")
        
        # 初始化AI实例管理器
        from app.ai.instances import ai_instance_manager
        instance_stats = ai_instance_manager.get_instance_stats()
        logger.info(f"✅ AI实例管理器初始化成功")
        logger.info(f"   活跃实例: {instance_stats['active_instances']}")
        logger.info(f"   总实例数: {instance_stats['total_instances']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ AI系统初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def start_application():
    """启动Flask应用"""
    logger.info("🚀 启动Flask应用...")
    
    try:
        # 使用现有的启动脚本
        start_script = os.path.join(PROJECT_ROOT, 'start_flask.py')
        if os.path.exists(start_script):
            logger.info(f"使用启动脚本: {start_script}")
            logger.info("应用启动后按 Ctrl+C 停止")
            
            # 直接执行启动脚本
            subprocess.run([sys.executable, start_script])
            return True
        else:
            # 如果没有启动脚本，直接启动应用
            logger.info("⚠️  未找到启动脚本，直接启动应用...")
            
            from app import app
            from app.config import Config
            
            logger.info(f"应用将在 http://0.0.0.0:{Config.PORT} 启动")
            logger.info("应用启动后按 Ctrl+C 停止")
            
            app.run(host='0.0.0.0', port=Config.PORT, debug=True)
            return True
    except KeyboardInterrupt:
        logger.info("✅ 应用已停止")
        return True
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("🚀 MTSCOS AI Project - 自动化初始化开始")
    logger.info(f"项目根目录: {PROJECT_ROOT}")
    
    # 解析命令行参数
    args = parse_args()
    
    # 执行初始化步骤
    steps = [
        ("环境检查", check_environment, True),
        ("依赖安装", install_dependencies, not args.skip_deps),
        ("目录结构创建", create_directories, True),
        ("数据库初始化", init_database, not args.skip_db),
        ("AI系统初始化", init_ai_system, not args.skip_ai),
    ]
    
    success = True
    for step_name, step_func, should_run in steps:
        if should_run:
            if not step_func():
                success = False
                logger.error(f"❌ {step_name}失败")
                # 询问是否继续
                if step_name != "环境检查":
                    continue_input = input(f"{step_name}失败，是否继续？(y/N): ").strip().lower()
                    if continue_input != 'y':
                        logger.info("初始化流程已停止")
                        sys.exit(1)
        else:
            logger.info(f"⏭️  跳过{step_name}")
    
    if success:
        logger.info("🎉 初始化流程完成！")
        
        # 如果指定了启动应用，就启动应用
        if args.start_app:
            start_application()
    else:
        logger.error("❌ 初始化流程失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()
