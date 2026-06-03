# -*- coding: utf-8 -*-
# 修改版启动脚本,用于修复learning.py中的MODEL_PATH KeyError问题
import logging
logger = logging.getLogger(__name__)
import sys
import os
import types

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. 首先应用猴子补丁,修复app.config模块
print("[启动修复] 应用配置猴子补丁...")

# 创建一个假的配置模块
fake_config = types.ModuleType('app.config')
fake_config.Config = type('Config', (), {
    'MODEL_PATH': 'models/',
    'AI_CONFIG': {
        'MONITORING_ENABLED': True,
        'LEARNING_ENABLED': True,
        'AUTO_ADAPT': True,
        'AI_ENHANCEMENT': True,
        'AUTO_OPTIMIZATION': True,
        'AUTO_CLOSURE': True,
        'SELF_OPTIMIZATION': True
    },
    'DEBUG': True,
    'SECRET_KEY': 'dev-secret-key',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///app.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'DATABASE_PATH': 'app.db',
    'AI_CONFIG_PATH': 'ai_config.json',
    'SYSTEM_CONFIG_PATH': 'system_config.json',
    'LOG_LEVEL': 'INFO',
    'LOG_SIZE_FILE': 'app.log',
    'LOG_TIME_FILE': 'time_rotated.log',
    'LOG_MAX_BYTES': 1024 * 1024 * 10,  # 10MB
    'LOG_BACKUP_COUNT': 7,
    'LOG_ROTATE_WHEN': 'D',  # 每天轮转
    'LOG_ROTATE_INTERVAL': 1,  # 轮转间隔
    'LOG_ROTATE_BACKUP_COUNT': 7,  # 保留的日志文件数量
    # 网络配置
    'NETWORK_CONFIG': {
        'MAX_CONNECTIONS': 100,
        'TIMEOUT': 30,
        'RETRY_COUNT': 3,
        'CACHE_SIZE': 1000,
        'CACHE_TTL': 3600
    },
    # 信道配置
    'CHANNEL_CONFIG': {
        'MAX_CHANNELS': 50,
        'CHANNEL_TIMEOUT': 60,
        'MAX_MSG_PER_CHANNEL': 1000
    }
})
fake_config.DEFAULT_CONFIG = {
    'AI_CONFIG': {
        'LEARNING_ENABLED': True,
        'AI_ENHANCEMENT': True,
        'AUTO_CLOSURE': True,
    }
}

sys.modules['app.config'] = fake_config
# 2. 现在尝试导入app.ai.learning模块,验证修复是否有效
try:
    print("[启动修复] learning模块修复成功!")
except Exception as e:
    print(f"[启动修复] learning模块修复失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 导入并运行原始的启动脚本
print("[启动修复] 启动原始服务器...")
try:
    print("[启动修复] 服务器启动脚本导入成功!")
except Exception as e:
    print(f"[启动修复] 服务器启动脚本导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
