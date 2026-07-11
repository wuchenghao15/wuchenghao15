#!/usr/bin/env python3
"""
核心初始化模块
- 创建Flask应用
- 注册Jinja2模板全局函数
- 配置中间件
- 初始化数据库连接
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask

logger = logging.getLogger(__name__)


def create_flask_app(config=None) -> Flask:
    """创建Flask应用实例"""
    logger.info("=" * 60)
    logger.info("[核心 1/4] 创建Flask应用...")
    logger.info("=" * 60)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 静态文件目录配置 - 在创建应用时直接传入，确保路由正确注册
    static_dir = os.path.join(base_dir, 'src', 'html', 'assets')
    if not os.path.exists(static_dir):
        static_dir = os.path.join(base_dir, 'static')
    template_dir = os.path.join(base_dir, 'templates')

    app = Flask(__name__,
                static_folder=static_dir,
                static_url_path='/assets',
                template_folder=template_dir)

    # 启用模板自动重载（开发环境）
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # 基础配置
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

    # 强制设置secret_key
    secret_key = os.environ.get('SECRET_KEY', 'mtscos_ai_secret_key_2026')
    app.secret_key = secret_key
    app.config['SECRET_KEY'] = secret_key

    # 应用从数据库配置加载器获取的配置
    if config:
        for key, value in config.items():
            if key.isupper() or key in ['SECRET_KEY', 'DEBUG']:
                app.config[key] = value
                if key == 'SECRET_KEY' and value:
                    app.secret_key = value

    logger.info(f"Flask应用创建成功")
    logger.info(f"  模板目录: {app.template_folder}")
    logger.info(f"  静态目录: {app.static_folder}")

    return app


def register_template_globals(app: Flask) -> Flask:
    """注册Jinja2模板全局函数"""
    logger.info("=" * 60)
    logger.info("[核心 2/4] 注册模板全局函数...")
    logger.info("=" * 60)

    # 角色名称映射
    role_names = {
        'super_admin': '超级管理员',
        'admin': '管理员',
        'hardware_admin': '硬件管理员',
        'hardware_vikey_admin': '硬件维凯管理员',
        'teacher': '教师',
        'student': '学生',
        'researcher': '研究员',
        'designer': '设计师',
        'user': '用户',
        'guest': '访客'
    }

    # 角色标签样式
    role_tag_classes = {
        'super_admin': 'tag-red',
        'admin': 'tag-purple',
        'hardware_admin': 'tag-blue',
        'hardware_vikey_admin': 'tag-blue',
        'teacher': 'tag-green',
        'student': 'tag-blue',
        'researcher': 'tag-yellow',
        'designer': 'tag-orange',
        'user': 'tag-gray',
        'guest': 'tag-gray'
    }

    def get_role_name(role):
        """获取角色中文名"""
        return role_names.get(role, role)

    def get_role_tag_class(role):
        """获取角色标签样式类"""
        return role_tag_classes.get(role, 'tag-gray')

    def format_datetime(dt_str):
        """格式化日期时间"""
        if not dt_str:
            return '-'
        try:
            if isinstance(dt_str, datetime):
                return dt_str.strftime('%Y-%m-%d %H:%M:%S')
            dt = datetime.fromisoformat(str(dt_str).replace('Z', ''))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return str(dt_str)

    def format_number(num):
        """格式化数字（千分位）"""
        try:
            return f"{int(num):,}"
        except (ValueError, TypeError):
            return str(num)

    # 注册到Jinja2
    app.jinja_env.globals['get_role_name'] = get_role_name
    app.jinja_env.globals['getRoleName'] = get_role_name
    app.jinja_env.globals['get_role_tag_class'] = get_role_tag_class
    app.jinja_env.globals['getRoleTagClass'] = get_role_tag_class
    app.jinja_env.globals['format_datetime'] = format_datetime
    app.jinja_env.globals['format_number'] = format_number

    # 注册全局变量
    app.jinja_env.globals['app_name'] = 'MTSCOS AI 智能考试系统'
    app.jinja_env.globals['app_version'] = '7.1.0'
    app.jinja_env.globals['app_code_name'] = 'Intelligent Modular Enhanced Edition'

    logger.info("模板全局函数注册完成")
    return app


def configure_cors(app: Flask) -> Flask:
    """配置CORS跨域"""
    logger.info("=" * 60)
    logger.info("[核心 3/4] 配置CORS跨域...")
    logger.info("=" * 60)

    try:
        from flask_cors import CORS
        CORS(app, resources={
            r"/api/*": {"origins": "*"},
            r"/auth/*": {"origins": "*"}
        })
        logger.info("CORS跨域配置启用")
    except ImportError:
        logger.warning("flask-cors 未安装，跳过CORS配置")

    return app


def init_database_connections(app: Flask) -> Flask:
    """初始化数据库连接"""
    logger.info("=" * 60)
    logger.info("[核心 4/4] 初始化数据库连接...")
    logger.info("=" * 60)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    split_db_dir = os.path.join(base_dir, 'split_databases')

    # 确保数据库目录存在
    os.makedirs(split_db_dir, exist_ok=True)

    # 统计数据库文件
    db_count = 0
    if os.path.exists(split_db_dir):
        for f in os.listdir(split_db_dir):
            if f.endswith('.db'):
                db_count += 1

    logger.info(f"分布式数据库目录: {split_db_dir}")
    logger.info(f"检测到 {db_count} 个数据库文件")

    # 保存到app配置
    app.config['SPLIT_DB_DIR'] = split_db_dir
    app.config['DB_COUNT'] = db_count
    app.config['DISTRIBUTED_MODE'] = True

    # 导入db_manager确保数据库连接可用
    try:
        sys.path.insert(0, base_dir)
        import db_manager
        app.config['DB_MANAGER'] = db_manager
        logger.info("数据库管理器加载成功")
    except Exception as e:
        logger.warning(f"数据库管理器加载失败: {e}")

    return app


def core_initialization(config=None) -> Flask:
    """核心初始化（4个步骤）"""
    logger.info("=" * 60)
    logger.info("开始核心初始化...")
    logger.info("=" * 60)

    start_time = datetime.now()

    # 步骤1: 创建Flask应用
    app = create_flask_app(config)

    # 步骤2: 注册模板全局函数
    app = register_template_globals(app)

    # 步骤3: 配置CORS
    app = configure_cors(app)

    # 步骤4: 初始化数据库连接
    app = init_database_connections(app)

    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info("=" * 60)
    logger.info(f"核心初始化完成！耗时: {elapsed:.2f}秒")
    logger.info("=" * 60)

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    app = core_initialization()
    print(f"\nFlask应用创建成功: {app.name}")
    print(f"路由数量: {len(list(app.url_map.iter_rules()))}")
