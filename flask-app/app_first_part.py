# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
MTSCOS AI Project Main Application
"""

import os
import sys
import logging
import traceback
import argparse
import sqlite3
import hashlib
import time
from contextlib import contextmanager
from datetime import datetime
from flask import jsonify, render_template, request, redirect, session

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置默认的MODEL_PATH环境变量
if 'MODEL_PATH' not in os.environ:
    os.environ['MODEL_PATH'] = './models'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS

# 创建Flask应用
app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'mtscos_ai_secret_key_2026'  # 设置session密钥

# 配置CORS支持
CORS(app, resources={r"/*": {"origins": "*"}})

# 导入配置API路由蓝图
from app.api.config_api import config_api_bp
app.register_blueprint(config_api_bp)

# 导入并注册监考API路由蓝图
from app.blueprints.proctor_api import proctor_api
app.register_blueprint(proctor_api)

# 导入并注册音频API路由蓝图
from app.blueprints.audio_api import audio_api
app.register_blueprint(audio_api)

# 导入并注册音频字库API路由蓝图
from app.blueprints.pronunciation_api import pronunciation_api
app.register_blueprint(pronunciation_api)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

# 初始化权限管理器和会话管理器
from app.utils.permission_manager import init_permission_manager
from app.utils.session_manager import init_session_manager
from app.utils.rule_manager import init_rule_manager
from app.utils.config_manager import init_config_manager
from app.utils.monitor_manager import init_monitor_manager
from app.utils.backup_manager import init_backup_manager
from app.middlewares.access_control import access_control_middleware

# 初始化权限管理器
init_permission_manager(DATABASE_PATH)
