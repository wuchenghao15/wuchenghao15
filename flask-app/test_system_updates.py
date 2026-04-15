#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系统自动更新和拓展功能
"""

import sys
from ai_employee_system import AIRouteSystem

def test_system_updates():
    """测试系统自动更新功能"""
    print("=== 测试系统自动更新功能 ===")
    
    # 启动AI路由系统
    ai_route = AIRouteSystem()
    ai_route.start()
    
    # 测试获取系统状态
    print("\n1. 测试获取系统状态...")
    status = ai_route.get_status()
    print(f"系统运行状态: {status['is_running']}")
    print(f"当前系统版本: {status['system_version']}")
    print(f"AI员工数量: {status['total_employees']}")
    
    # 测试自动更新系统
    print("\n2. 测试自动更新系统...")
    update_result = ai_route.auto_update_system({})
    print(f"更新结果: {update_result['success']}")
    print(f"更新消息: {update_result['message']}")
    if update_result['success']:
        print(f"新版本: {update_result['new_version']}")
        print(f"最后更新: {update_result['last_update']}")
        print(f"修复结果数量: {len(update_result['repair_results'])}")
    
    # 测试系统拓展功能
    print("\n3. 测试系统拓展功能...")
    expand_result = ai_route.expand_system({})
    print(f"拓展结果: {expand_result['success']}")
    print(f"拓展消息: {expand_result['message']}")
    if expand_result['success']:
        print(f"拓展结果数量: {len(expand_result['expansion_results'])}")
        for i, result in enumerate(expand_result['expansion_results']):
            print(f"  {i+1}. 组件: {result['component']}, 操作: {result['action']}, 成功: {result['success']}")
    
    # 再次获取系统状态，查看更新后的状态
    print("\n4. 测试获取更新后的系统状态...")
    new_status = ai_route.get_status()
    print(f"系统运行状态: {new_status['is_running']}")
    print(f"更新后系统版本: {new_status['system_version']}")
    print(f"AI员工数量: {new_status['total_employees']}")
    
    # 停止AI路由系统
    ai_route.stop()
    print("\n系统已停止")

def main():
    """主函数"""
    print("开始测试系统自动更新和拓展功能...")
    
    try:
        test_system_updates()
        print("\n=== 所有测试完成 ===")
        print("系统自动更新和拓展功能测试通过！")
        return 0
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
