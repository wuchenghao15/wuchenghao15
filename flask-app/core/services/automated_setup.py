# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
MTSCOS AI Project - 自动化初始化脚本

这个脚本提供了项目的统一自动化初始化流程,包括:
5. AI系统初始化
6. 应用启动

用法:
    python3 automated_setup.py [--skip-deps] [--skip-db] [--skip-ai] [--start-app]

选项:
    --skip-deps       跳过依赖安装
    --skip-db         跳过数据库初始化
    --skip-ai         跳过AI系统初始化
    --start-app       初始化完成后启动应用
    --help            显示帮助信息
r"""

import os
import sys
import logging
import argparse
import subprocess
import time

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(r'automated_setup')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, PROJECT_ROOT)


def parse_args():
    parser = argparse.ArgumentParser(description=r'MTSCOS AI Project - 自动化初始化脚本')
    parser.add_argument(r'--skip-deps', action=r'store_true', help=r'跳过依赖安装')
    parser.add_argument(r'--skip-db', action=r'store_true', help=r'跳过数据库初始化')
    parser.add_argument(r'--skip-ai', action=r'store_true', help=r'跳过AI系统初始化')
    parser.add_argument(r'--start-app', action=r'store_true', help=r'初始化完成后启动应用')
    return parser.parse_args()


def check_environment():
    logger.info(r"🔍 检查系统环境...")

    python_version = sys.version_info
    if python_version < (3, 7):
        logger.error(fr"❌ Python版本过低,需要3.7+,当前版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        return False
    logger.info(fr"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")

    try:
        import pip
        logger.info(r"✅ pip已安装")
    except ImportError:
        logger.error(r"❌ pip未安装")
        return False
    required_dirs = [r'app', r'static', r'templates', r'config']
    for dir_name in required_dirs:
        dir_path = os.path.join(PROJECT_ROOT, dir_name)
        if not os.path.exists(dir_path):
            logger.warning(fr"⚠️ 目录不存在: {dir_path}")
            try:
                os.makedirs(dir_path)
            except Exception as e:
                logger.error(fr"❌ 创建目录失败: {dir_path}, 错误: {str(e)}")
                return False
    config_files = [r'app/config.py', r'requirements.txt']
    for file_path in config_files:
        full_path = os.path.join(PROJECT_ROOT, file_path)
        if not os.path.exists(full_path):
            logger.warning(fr"⚠️ 配置文件不存在: {full_path}")

    logger.info(r"✅ 环境检查完成")
    return True


def install_dependencies():
    logger.info(r"📦 安装项目依赖...")

    requirements_file = os.path.join(PROJECT_ROOT, r'requirements.txt')
    if not os.path.exists(requirements_file):
        logger.warning(fr"⚠️ 依赖文件不存在: {requirements_file}")
        return True

    try:
        result = subprocess.run(
            [sys.executable, r'-m', r'pip', r'install', r'-r', requirements_file],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.debug(fr"安装输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(fr"❌ 依赖安装失败: {e.stderr}")
        return False


def init_database():
    logger.info(r"🗄️  初始化数据库...")

    try:
        init_script = os.path.join(PROJECT_ROOT, r'init_and_update_db.py')
        if os.path.exists(init_script):
            result = subprocess.run(
                [sys.executable, init_script],
                check=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                logger.debug(fr"数据库初始化输出: {result.stdout}")
        else:
            from app.models.system_config import SystemConfig
            from app.models.logs import LogEntry
            from app.models.ai import AIInstance
            from app.models.local_data import LocalData

            SystemConfig.create_table()
            LogEntry.create_table()
            AIInstance.create_table()
            LocalData.create_table()

            logger.info(r"✅ 所有数据库表创建成功")

            update_script = os.path.join(PROJECT_ROOT, r'update_database.py')
            if os.path.exists(update_script):
                result = subprocess.run(
                    [sys.executable, update_script],
                    check=True,
                    capture_output=True,
                    text=True
                )

        return True
    except Exception as e:
        logger.error(fr"❌ 数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def create_directory_structure():
    logger.info(r"📁 创建必要的目录结构...")
    directories = [
        r'data',
        r'backups',
        r'static/avatars',
        r'static/js',
        r'static/js/vikey',
        r'static/js/utils',
        r'templates',
        r'instance',
        r'docs'
    ]
    for dir_path in directories:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
                logger.info(fr"✅ 创建目录: {full_path}")
            except Exception as e:
                logger.error(fr"❌ 创建目录失败: {full_path}, 错误: {str(e)}")
                return False

    logger.info(r"✅ 目录结构创建完成")
    return True


def init_ai_system():
    logger.info(r"🤖 初始化AI系统...")
    try:
        from app.ai.ensemble import AIEnsemble
        ai_ensemble = AIEnsemble()
        logger.info(fr"✅ AI集初始化成功: {ai_ensemble.ensemble_id}")
        logger.info(fr"   项目功能: {ai_ensemble.project_features}")
        logger.info(fr"   所需AI类型: {ai_ensemble.required_ai_types}")

        from app.ai.instances import ai_instance_manager
        instance_stats = ai_instance_manager.get_stats()
        logger.info(f"   活跃实例: {instance_stats[r'active_instances']}r")
        logger.info(f"   总实例数: {instance_stats[r'total_instances']}r")

        return True
    except Exception as e:
        logger.error(f"❌ AI系统初始化失败: {str(e)}r")
        import traceback
        traceback.print_exc()
        return False


def start_application():
    logger.info("🚀 启动Flask应用...")

    try:
        start_script = os.path.join(PROJECT_ROOT, r'start_flask.py')
        if os.path.exists(start_script):
            logger.info(fr"使用启动脚本: {start_script}")
            subprocess.run([sys.executable, start_script])
            return True
        else:
            logger.info(r"⚠️  未找到启动脚本,直接启动应用...")

            from app import app
            from app.config import Config

            logger.info(fr"应用将在 http://0.0.0.0:{Config.PORT} 启动")
            logger.info(r"应用启动后按 Ctrl+C 停止")

            # 安全修复：通过环境变量控制debug模式
            app.run(host=r'127.0.0.1', port=Config.PORT, debug=os.environ.get(r'FLASK_DEBUG', r'0') == r'1')
            return True
    except KeyboardInterrupt:
        logger.info(r"✅ 应用已停止")
        return True
    except Exception as e:
        logger.error(fr"❌ 启动应用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    logger.info(fr"项目根目录: {PROJECT_ROOT}")

    args = parse_args()

    steps = [
        (r"环境检查", check_environment, True),
        (r"依赖安装", install_dependencies, not args.skip_deps),
        (r"数据库初始化", init_database, not args.skip_db),
        (r"目录结构创建", create_directory_structure, True),
        (r"AI系统初始化", init_ai_system, not args.skip_ai),
    ]
    success = True
    for step_name, step_func, should_run in steps:
        if should_run:
            if not step_func():
                success = False
                logger.error(fr"❌ {step_name}失败")
                if step_name != r"环境检查":
                    continue_input = input(fr"{step_name}失败,是否继续?(y/N): ").strip().lower()
                    if continue_input != r'y':
                        logger.info(r"初始化流程已停止")
                        sys.exit(1)
        else:
            logger.info(fr"⏭️  跳过{step_name}")

    if success:
        logger.info(r"🎉 初始化流程完成!")

        if args.start_app:
            start_application()
    else:
        sys.exit(1)


if __name__ == r'__main__':
    main()
