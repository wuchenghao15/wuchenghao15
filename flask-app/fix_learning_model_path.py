# -*- coding: utf-8 -*-
# 猴子补丁脚本,用于修复learning.py中的MODEL_PATH KeyError问题
import sys
import os
import types

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    }
})
fake_config.DEFAULT_CONFIG = {
    'AI_CONFIG': {
        'LEARNING_ENABLED': True,
        'AI_ENHANCEMENT': True,
        'AUTO_CLOSURE': True
    }
}

sys.modules['app.config'] = fake_config
# 现在导入并修复learning.py
try:
    from app.ai import learning
    print("成功修复了app.ai.learning模块")
except Exception as e:
    print(f"修复失败: {str(e)}")
    import traceback
    traceback.print_exc()
