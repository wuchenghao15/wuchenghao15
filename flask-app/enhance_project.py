#!/usr/bin/env python3
"""
项目功能增强脚本
用于自动强化项目功能，包括健康检查、性能监控、自动备份等

import os
import sys
# JSON import removed - using database
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_enhancement.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_project_structure() -> Dict[str, bool]:
    检查项目结构完整性

    Returns:
        项目结构检查结果字典
    logger.info("检查项目结构...")

    required_dirs = [
        'app',
        'static',
        'static/css',
        'static/js',
        'templates',
        'logs'
    ]

    required_files = [
        'app/__init__.py',
        'app/config.py',
        'app/routes/__init__.py',
        'static/css/style.css',
        'templates/base.html',
        'templates/index.html',
        'standalone_server.py'
    ]

    results = {}

    for dir_path in required_dirs:
        results[f'dir_{dir_path}'] = os.path.exists(dir_path)

    for file_path in required_files:
        results[f'file_{file_path}'] = os.path.exists(file_path)

    return results

def fix_project_structure() -> None:
    修复项目结构
    logger.info("修复项目结构...")

    # 创建缺失的目录
    required_dirs = [
        'logs',
        'static/css',
        'static/js',
        'static/img',
        'app/ai',
        'app/utils'

        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"创建目录: {dir_path}")

    # 创建缺失的基础文件
    if not os.path.exists('app/__init__.py'):
        with open('app/__init__.py', 'w') as f:
        logger.info("创建文件: app/__init__.py")

    if not os.path.exists('app/routes/__init__.py'):
        with open('app/routes/__init__.py', 'w') as f:
            f.write('''from flask import Blueprint\n\nbp = Blueprint('main', __name__)\n\nfrom app.routes import main\n''')
        logger.info("创建文件: app/routes/__init__.py")

    if not os.path.exists('app/config.py'):
        with open('app/config.py', 'w') as f:
            f.write('''class Config:\n    SECRET_KEY = 'your-secret-key-here'\n    VERSION = '1.0.0'\n    ENV = 'development'\n    DEBUG = True\n''')
        logger.info("创建文件: app/config.py")

def enhance_security() -> None:
    增强项目安全性
    logger.info("增强项目安全性...")

    # 更新配置文件，添加安全设置
    if os.path.exists('app/config.py'):
        with open('app/config.py', 'r') as f:
            content = f.read()

        # 添加安全相关配置
        security_configs = [
            '    # 安全配置\n',
            '    SESSION_COOKIE_SECURE = True\n',
            '    SESSION_COOKIE_HTTPONLY = True\n',
            '    SESSION_COOKIE_SAMESITE = 'strict'\n',
            '    PERMANENT_SESSION_LIFETIME = 3600  # 1小时\n',
            '    WTF_CSRF_ENABLED = True\n',
            '    WTF_CSRF_TIME_LIMIT = 3600\n',
            '    \n',
            '    # 密码哈希配置\n',
            '    BCRYPT_LOG_ROUNDS = 12\n',
        ]

        if 'SESSION_COOKIE_SECURE' not in content:
            content += ''.join(security_configs)
            with open('app/config.py', 'w') as f:
                f.write(content)
            logger.info("更新安全配置")

    # 创建安全中间件
    middleware_path = 'app/utils/security.py'
    if not os.path.exists(middleware_path):
        with open(middleware_path, 'w') as f:
            f.write('''from flask import request, g\nimport time\n\n\ndef security_middleware(app):\n    @app.before_request\n    def before_request():\n        # 记录请求开始时间\n        g.start_time = time.time()\n        \n        # 安全头设置\n        response.headers['X-Content-Type-Options'] = 'nosniff'\n        response.headers['X-Frame-Options'] = 'DENY'\n        response.headers['X-XSS-Protection'] = '1; mode=block'\n        response.headers['Content-Security-Policy'] = "default-src 'self'"\n    \n    @app.after_request\n    def after_request(response):\n        # 计算请求处理时间\n        if hasattr(g, 'start_time'):\n            response_time = time.time() - g.start_time\n            app.logger.info(f'Request processed in {response_time:.3f}s')\n        return response\n''')
        logger.info("创建安全中间件: app/utils/security.py")

    添加健康检查功能
    logger.info("添加健康检查功能...")

    # 添加健康检查路由
    health_route = '''\n@bp.route('/health')\ndef health_check():\n    """健康检查端点"""\n    return {\n        'status': 'healthy',\n        'timestamp': datetime.utcnow().isoformat(),\n        'version': current_app.config.get('VERSION', 'unknown'),\n        'service': 'MTSCOS AI System'\n    }\n'''

    routes_file = 'app/routes/main.py'
    if os.path.exists(routes_file):
        with open(routes_file, 'r') as f:
            content = f.read()

        if '/health' not in content:
            with open(routes_file, 'a') as f:
                f.write(health_route)
            logger.info("添加健康检查路由")
    else:
        with open(routes_file, 'w') as f:
            f.write('''from flask import current_app, jsonify\nfrom datetime import datetime\nfrom app.routes import bp\n\n''' + health_route)
        logger.info("创建路由文件并添加健康检查")

def add_performance_monitoring() -> None:
    添加性能监控功能
    logger.info("添加性能监控功能...")
    # 创建性能监控脚本
    monitor_script = '''#!/usr/bin/env python3
性能监控脚本
定期检查系统性能并记录日志

import psutil
import time

# 配置日志
logging.basicConfig(
    filename='logs/performance.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

    """监控系统性能"""
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)

        mem = psutil.virtual_memory()
        mem_usage = mem.percent
        # 获取磁盘使用率
        disk_usage = disk.percent

        net = psutil.net_io_counters()

        logging.info(f"CPU: {cpu_usage}% | MEM: {mem_usage}% | DISK: {disk_usage}% | "
                     f"NET IN: {net.bytes_recv/1024/1024:.2f} MB | NET OUT: {net.bytes_sent/1024/1024:.2f} MB")

        # 每60秒检查一次
        time.sleep(60)

if __name__ == "__main__":
    monitor_performance()
'''

    with open('performance_monitor.py', 'w') as f:
        f.write(monitor_script)

    os.chmod('performance_monitor.py', 0o755)
    logger.info("创建性能监控脚本: performance_monitor.py")

def add_auto_backup() -> None:
    添加自动备份功能
    logger.info("添加自动备份功能...")

    # 创建备份脚本
    backup_script = '''#!/usr/bin/env python3
自动备份脚本
定期备份数据库和重要文件

import shutil
import zipfile

# 配置日志
logging.basicConfig(
    filename='logs/backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def create_backup():
    """创建备份"""
    # 创建备份目录
    backup_dir = 'backups'

    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
    # 要备份的目录和文件
    items_to_backup = [
        'templates',
        'static',
        'config.py',
    ]

        # 创建ZIP文件
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in items_to_backup:
                    # 备份文件
                    zipf.write(item, os.path.basename(item))
                    logging.info(f"备份文件: {item}")
                    # 备份目录
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, '.')
                            zipf.write(file_path, arcname)

        logging.info(f"备份成功: {backup_file}")

        # 清理旧备份（保留最近10个）
        backups = sorted(os.listdir(backup_dir), reverse=True)
        if len(backups) > 10:
            for old_backup in backups[10:]:
                os.remove(os.path.join(backup_dir, old_backup))
                logging.info(f"清理旧备份: {old_backup}")
    except Exception as e:
        logging.error(f"备份失败: {str(e)}")
if __name__ == "__main__":
'''

    with open('backup_script.py', 'w') as f:
        f.write(backup_script)

    os.chmod('backup_script.py', 0o755)
    logger.info("创建自动备份脚本: backup_script.py")

def update_requirements() -> None:
    更新项目依赖
    logger.info("更新项目依赖...")

    # 基础依赖列表
    requirements = [
        'Flask>=2.0.0',
        'Flask-Bcrypt>=0.7.1',
        'Flask-Cors>=3.0.10',
        'Flask-Login>=0.5.0',
        'Flask-WTF>=1.0.0',
        'gunicorn>=20.1.0',
        'psutil>=5.9.0',
        'python-dotenv>=0.19.0',
        'requests>=2.26.0',
        'pytz>=2021.3'
    ]

    # 写入requirements.txt
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(requirements) + '\n')

    logger.info("更新依赖文件: requirements.txt")

def add_logging_config() -> None:
    添加日志配置
    logger.info("添加日志配置...")

    # 更新app/__init__.py添加日志配置
    if os.path.exists('app/__init__.py'):
        with open('app/__init__.py', 'r') as f:
            content = f.read()


        if 'RotatingFileHandler' not in content:
            with open('app/__init__.py', 'a') as f:
                f.write(logging_config)
            logger.info("添加日志配置到app/__init__.py")

def enhance_cors() -> None:
    增强CORS配置
    logger.info("增强CORS配置...")

    # 更新app/__init__.py添加CORS支持
    if os.path.exists('app/__init__.py'):
        with open('app/__init__.py', 'r') as f:
            content = f.read()

        if 'CORS' not in content:
            # 添加CORS导入和配置
            content = content.replace('from flask import Flask', 'from flask import Flask\nfrom flask_cors import CORS')
            content += '\n\n# 配置CORS\nCORS(app)\n'

            with open('app/__init__.py', 'w') as f:
                f.write(content)
            logger.info("添加CORS配置")

def main() -> None:
    主函数
    logger.info("开始增强项目功能...")

    # 1. 检查项目结构
    structure_results = check_project_structure()
    logger.info(f"项目结构检查结果: {structure_results}")

    # 2. 修复项目结构
    fix_project_structure()

    # 3. 增强安全性
    enhance_security()

    # 4. 添加健康检查
    add_health_check()
    # 5. 添加性能监控
    add_performance_monitoring()

    # 6. 添加自动备份
    add_auto_backup()

    # 7. 更新依赖
    update_requirements()

    # 8. 添加日志配置
    add_logging_config()

    # 9. 增强CORS配置
    enhance_cors()

    logger.info("项目功能增强完成！")

    report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'completed',
            '安全性增强',
            '健康检查功能',
            '性能监控',
            '自动备份',
            '依赖更新',
            'CORS增强'
        ]
    }

    with open('enhancement_report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info("生成增强报告: enhancement_report.json")

if __name__ == "__main__":
    main()
