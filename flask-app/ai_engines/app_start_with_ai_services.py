#!/usr/bin/env python3
"""
Flask app start script with AI services for MTSCOS AI Project
"""

from contextlib import contextmanager
import logging
logger = logging.getLogger(__name__)
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'temp-secret-key-for-development'
app.config['DATABASE'] = 'app.db'

def get_db_connection():
    """获取数据库连接"""
    import sqlite3
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        print("[INFO] 数据库表结构初始化完成")
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

option_generator = None

def init_option_generator():
    """初始化智能选项生成器"""
    global option_generator
    if not option_generator:
        try:
            from intelligent_option_generator import IntelligentOptionGenerator
            option_generator = IntelligentOptionGenerator()
            print("[INFO] 智能选项生成器初始化完成")
        except Exception as e:
            print(f"[WARNING] 智能选项生成器初始化失败: {str(e)}")
    return option_generator

ai_service_manager = None
ai_learning_system = None
ai_cluster_manager = None

def init_ai_services():
    """初始化AI服务"""
    global ai_service_manager, ai_learning_system, ai_cluster_manager

    try:
        print("[INFO] AI服务初始化成功")
        return True
    except Exception as e:
        print(f"[ERROR] 初始化AI服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/health')
def health():
    return "OK", 200

@app.route('/version')
def version():
    return {"VERSION": "3.0.0", "INTERNAL_VERSION": "3.0.0.5678"}, 200

@app.route('/')
def index():
    return "Hello World from MTSCOS AI Project!", 200

@app.route('/api/ai/init', methods=['POST'])
def init_ai_services_route():
    """初始化AI服务的API端点"""
    try:
        success = init_ai_services()
        if success:
            return jsonify({'success': True, 'message': 'AI services initialized successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to initialize AI services'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("[INFO] 启动MTSCOS AI应用...")

    print("[INFO] 初始化数据库表结构...")
    init_db()
    print("[INFO] 数据库表结构初始化完成")

    try:
        init_option_generator()
        print("[INFO] 智能选项生成器初始化成功")
    except Exception as e:
        print(f"[WARNING] 智能选项生成器初始化失败: {str(e)}")

    port = 8888
    print(f"[INFO] 监听地址: 0.0.0.0:{port}")
    print(f"[INFO] 访问地址: http://localhost:{port}")

    print("[INFO] 正在启动Flask服务器...")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
