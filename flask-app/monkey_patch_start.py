# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
使用Monkey Patching技术修复MODEL_PATH KeyError问题的启动脚本

import logging
logger = logging.getLogger(__name__)
import os
import sys
import builtins

# 首先设置MODEL_PATH环境变量
print("设置MODEL_PATH环境变量...")
os.environ['MODEL_PATH'] = './models'
print(f"MODEL_PATH已设置为: {os.environ['MODEL_PATH']}")

# 修改sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 保存原始的__import__函数
original_import = builtins.__import__

# 定义Monkey Patch版本的__import__函数
def patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    # 在导入app.ai.learning之前,确保Config类有MODEL_PATH属性
    if name == 'app.ai.learning' or 'ai.learning' in name:
        print(f"拦截对 {name} 的导入,先修复Config.MODEL_PATH...")
        try:
            # 先导入config模块
            config_module = original_import('app.config', globals, locals, fromlist=('Config',), level=0)
            # 确保Config类有MODEL_PATH属性
            if hasattr(config_module, 'Config'):
                if not hasattr(config_module.Config, 'MODEL_PATH'):
                    config_module.Config.MODEL_PATH = './models'
                    print(f"已添加Config.MODEL_PATH = './models'")
        except Exception as e:
            print(f"修复Config.MODEL_PATH时出错: {e}")

    # 调用原始的__import__函数
    return original_import(name, globals, locals, fromlist, level)

# 应用Monkey Patch
builtins.__import__ = patched_import

# 现在尝试导入app模块
print("尝试导入app模块...")
try:
    print("app模块导入成功!")

    # 启动服务器
    print("启动服务器...")
    # 从配置获取服务器参数
    host = app.config.get('SERVER_HOST', '0.0.0.0')
    port = app.config.get('SERVER_PORT', 8888)
    debug = app.config.get('DEBUG', True)
    protocol = app.config.get('PROTOCOL', 'http')
    version = app.config.get('VERSION', '1.0.0')

    print(f"Starting MTSCOS AI Integrated Server v{version}...")
    print(f"Server will run on {protocol}://{host}:{port}")
    print(f"Environment: {app.config.get('ENV', 'development')}")

    # 使用集成的应用实例运行服务器
    app.run(host=host, port=port, debug=debug, use_reloader=False)
except Exception as e:
    print(f"导入app模块或启动服务器时出错: {e}")
    traceback.print_exc()
    sys.exit(1)

"""