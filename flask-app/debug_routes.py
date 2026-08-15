#!/usr/bin/env python3
"""调试路由注册问题"""

import sys
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app')

print("=" * 60)
print("调试路由注册问题")
print("=" * 60)

# 测试1: 直接创建Flask应用并注册Blueprint
from flask import Flask
from app.api.exam_enhancement_api import exam_enhancement_api

app1 = Flask('test_app1')
app1.register_blueprint(exam_enhancement_api)

routes_before = [str(rule) for rule in app1.url_map.iter_rules()]
enhanced_routes_before = [r for r in routes_before if 'enhanced' in r]

print(f"\n测试1 - 直接注册Blueprint:")
print(f"  总路由数: {len(routes_before)}")
print(f"  exam/enhanced路由数: {len(enhanced_routes_before)}")
if enhanced_routes_before:
    print(f"  示例路由: {enhanced_routes_before[:3]}")

# 测试2: 导入app.py中的app实例
print(f"\n测试2 - 从app.py导入app实例:")
try:
    # 模拟导入app.py的app实例
    import importlib.util
    spec = importlib.util.spec_from_file_location("real_app", "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.py")
    real_app_module = importlib.util.module_from_spec(spec)
    
    print(f"  导入app.py模块...")
    spec.loader.exec_module(real_app_module)
    
    app2 = real_app_module.app
    routes_after = [str(rule) for rule in app2.url_map.iter_rules()]
    enhanced_routes_after = [r for r in routes_after if 'enhanced' in r]
    
    print(f"  总路由数: {len(routes_after)}")
    print(f"  exam/enhanced路由数: {len(enhanced_routes_after)}")
    if enhanced_routes_after:
        print(f"  示例路由: {enhanced_routes_after[:3]}")
    else:
        print(f"  ✗ 未找到exam/enhanced路由")
        
except Exception as e:
    print(f"  ✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("调试完成")
print("=" * 60)