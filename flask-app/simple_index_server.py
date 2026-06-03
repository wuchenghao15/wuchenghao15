# -*- coding: utf-8 -*-
from contextlib import contextmanager
#!/usr/bin/env python3
"""
简化的索引服务器,只启动基本的Flask应用,用于诊断index页面访问问题

import sys
import os
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接启动服务器,跳过所有修复
try:
    from flask import Flask, render_template
    import os

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(__name__)
    # 创建一个简单的Flask应用

    app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

    # 主路由
    @app.route('/')
    def index():
        # 从数据库获取版本号
        version = '1.0.0'  # 默认版本号
        try:
            import sqlite3
            import os
            # 获取数据库路径
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
            print(f"数据库路径: {db_path}")

            # 连接数据库
            cursor = conn.cursor()
            print("数据库连接成功")

            # 确保系统配置表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    config_type TEXT NOT NULL DEFAULT 'string',
                    description TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("系统配置表检查完成")

            # 获取版本号
            cursor.execute('SELECT config_value FROM system_config WHERE config_key=? AND is_active=1', ('system_version',))
            row = cursor.fetchone()
            if row:
                version = row[0]
                print(f"从数据库获取到的版本号: {version}")
            else:
                # 如果没有版本号配置,创建一个
                cursor.execute('''
                    INSERT INTO system_config
                    (config_key, config_value, config_type, description, is_active)
                    VALUES (?, ?, ?, ?, 1)
                ''', ('system_version', version, 'string', '系统版本号'))
                conn.commit()
                print(f"创建了新的版本号配置: {version}")

            # 关闭连接
            conn.close()
            print("数据库连接关闭")
            # 如果出错,使用默认版本号
            print(f"获取版本号失败: {e}")
        # 传递版本号给模板
        print(f"传递给模板的版本号: {version}")
        return render_template('index.html', versions={'system_version': version})

    # 启动服务器
    port = 8888
    logger.info(f"简化索引服务器启动成功,访问地址: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

except Exception as e:
    logger.error(f"简化索引服务器启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

"""