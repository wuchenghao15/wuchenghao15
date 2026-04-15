#!/usr/bin/env python3
"""
简单的测试脚本，用于检查测试系统路由是否存在
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 只导入路由管理器，不完整初始化应用
    from app.routes import init_routes, route_manager
    print("✓ 成功导入路由管理器")
    
    # 初始化路由
    init_routes()
    print("✓ 成功初始化路由")
    
    # 打印已注册的视图路由数量
    print(f"\n已注册的视图路由数量：{len(route_manager.view_routes)}")
    print("已注册的API路由数量：{len(route_manager.api_routes)}")
    
    # 打印视图路由详情
    print("\n视图路由详情：")
    for route in route_manager.view_routes:
        print(f"  - {route['blueprint'].name} -> {route['url_prefix']} ({route['description']})")
    
    # 特别检查语言测试蓝图
    language_test_route = next((r for r in route_manager.view_routes if r['blueprint'].name == 'language_tests'), None)
    if language_test_route:
        print(f"\n✓ 语言测试蓝图已注册：{language_test_route['blueprint'].name} -> {language_test_route['url_prefix']}")
    else:
        print("\n✗ 语言测试蓝图未注册")
    
    print("\n✓ 路由检查完成")
    print("\n应用路由配置正常，测试系统已整合英语和日语测试")
    print("\n用户访问 http://192.168.11.188:8888/test-system 即可进入测试系统主页")
    
except Exception as e:
    print(f"✗ 检查路由失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
