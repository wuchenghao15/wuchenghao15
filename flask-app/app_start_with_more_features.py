#!/usr/bin/env python3
"""
Flask app start script with more features for MTSCOS AI Project

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# 创建Flask应用
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'temp-secret-key-for-development'
app.config['DATABASE'] = 'app.db'

# 初始化SQLite连接
def get_db_connection():
    """获取数据库连接"""
    import sqlite3
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

# 初始化数据库
def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 创建用户表（如果不存在）
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

# 定义简单的健康检查路由
@app.route('/health')
def health():
    return "OK", 200

# 定义版本路由
@app.route('/version')
def version():
    return {"VERSION": "3.0.0", "INTERNAL_VERSION": "3.0.0.5678"}, 200

# 定义根路由
@app.route('/')
def index():
    return "Hello World from MTSCOS AI Project!", 200

if __name__ == '__main__':
    print("[INFO] 启动MTSCOS AI应用...")

    # 初始化数据库表结构
    print("[INFO] 初始化数据库表结构...")
    init_db()
    print("[INFO] 数据库表结构初始化完成")
    # 尝试导入智能选项生成器
    print("[INFO] 导入智能选项生成器...")
    try:
        print("[INFO] 智能选项生成器导入成功")

        # 初始化智能选项生成器
        print("[INFO] 初始化智能选项生成器...")
        option_generator = IntelligentOptionGenerator()
        print("[INFO] 智能选项生成器初始化成功")
    except Exception as e:
        print(f"[WARNING] 智能选项生成器初始化失败: {str(e)}")

    port = 8888

    print(f"[INFO] 监听地址: 0.0.0.0:{port}")
    print(f"[INFO] 访问地址: http://localhost:{port}")

    # 启动服务器
    print("[INFO] 正在启动Flask服务器...")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
