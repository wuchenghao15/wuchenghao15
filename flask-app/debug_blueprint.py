# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
调试蓝图注册问题

import logging
logger = logging.getLogger(__name__)
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

print("调试集成设计蓝图注册问题...")
print("当前工作目录:", os.getcwd())
print("Python路径:", sys.path)

# 尝试直接导入蓝图模块
print("\n尝试导入集成设计蓝图模块...")
try:
    print("✓ 成功导入app.views.integrated_design模块")

    # 检查模块中的属性
    print("\n模块属性:")
    for attr in dir(app.views.integrated_design):
        if not attr.startswith('_'):
            print(f"  {attr}")

    # 检查蓝图对象
    print("\n检查蓝图对象...")
    if hasattr(app.views.integrated_design, 'integrated_design_bp'):
        blueprint = getattr(app.views.integrated_design, 'integrated_design_bp')
        print(f"✓ 找到蓝图对象: {blueprint}")
        print(f"  蓝图名称: {blueprint.name}")
        print(f"  蓝图URL前缀: {blueprint.url_prefix}")
        print(f"  蓝图规则数量: {len(blueprint.deferred_functions)}")
    else:
        print("✗ 没有找到integrated_design_bp对象")

except Exception as e:
    print(f"✗ 导入模块失败: {str(e)}")
    import traceback
    traceback.print_exc()

"""