#!/usr/bin/env python3
"""
基于环境变量的启动脚本，用于修复MODEL_PATH KeyError问题
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[环境变量启动] 正在初始化...")

# 1. 设置必要的环境变量
print("[环境变量启动] 设置环境变量...")
os.environ['MODEL_PATH'] = 'models/'
os.environ['AI_CONFIG'] = '''{
    "MONITORING_ENABLED": true,
    "LEARNING_ENABLED": true,
    "AUTO_ADAPT": true,
    "AI_ENHANCEMENT": true,
    "AUTO_OPTIMIZATION": true,
    "AUTO_CLOSURE": true,
    "SELF_OPTIMIZATION": true
}'''

# 2. 重写app.config模块的导入，使其首先检查环境变量
print("[环境变量启动] 重写配置导入机制...")

# 创建一个新的app.config模块
import types
new_config = types.ModuleType('app.config')

# 从原始配置模块导入所有内容，然后用环境变量覆盖
print("[环境变量启动] 加载原始配置...")
try:
    # 保存原始的sys.modules['app.config']
    original_config = None
    if 'app.config' in sys.modules:
        original_config = sys.modules['app.config']
    
    # 删除原始的app.config模块，以便重新导入
    if 'app.config' in sys.modules:
        del sys.modules['app.config']
    
    # 导入原始配置
    
    # 创建一个新的Config类，继承自原始的Config类
    class PatchedConfig(original_app_config.Config):
        # 从环境变量获取配置
        MODEL_PATH = os.environ.get('MODEL_PATH', 'models/')
        
        # 添加其他必要的配置项
        LOG_SIZE_FILE = 'app.log'
        LOG_TIME_FILE = 'time_rotated.log'
        LOG_MAX_BYTES = 1024 * 1024 * 10
        LOG_BACKUP_COUNT = 7
        LOG_ROTATE_WHEN = 'D'
        LOG_ROTATE_INTERVAL = 1
        LOG_ROTATE_BACKUP_COUNT = 7
        
        # 网络配置
        NETWORK_CONFIG = {
            'MAX_CONNECTIONS': 100,
            'TIMEOUT': 30,
            'RETRY_COUNT': 3,
            'CACHE_SIZE': 1000,
            'CACHE_TTL': 3600
        }
        
        # 信道配置
        CHANNEL_CONFIG = {
            'MAX_CHANNELS': 50,
            'CHANNEL_TIMEOUT': 60,
            'MAX_MSG_PER_CHANNEL': 1000
        }
    
    # 更新app.config模块
    new_config.Config = PatchedConfig
    new_config.DEFAULT_CONFIG = original_app_config.DEFAULT_CONFIG
    new_config.DEFAULT_CONFIG['MODEL_PATH'] = os.environ.get('MODEL_PATH', 'models/')
    
    # 替换sys.modules中的app.config
    sys.modules['app.config'] = new_config
    
    print("[环境变量启动] 配置补丁应用成功")
except Exception as e:
    print(f"[环境变量启动] 配置补丁应用失败: {e}")
    # 如果原始配置存在，恢复它
    if original_config:
        sys.modules['app.config'] = original_config

# 3. 尝试启动服务器
print("[环境变量启动] 正在启动服务器...")
try:
    # 导入并运行原始的start_server.py
    print("[环境变量启动] 服务器启动成功！")
except Exception as e:
    print(f"[环境变量启动] 服务器启动失败: {e}")
    import traceback
    traceback.print_exc()
