#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI管理系统

import sys
import os
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.ai_management_system import ai_management_system

def main():
    """主函数"""
    print("AI管理系统测试开始")

    # 启动系统
    print("\n1. 启动AI管理系统")
    success = ai_management_system.start()
    print(f"启动结果: {'成功' if success else '失败'}")

    # 测试创建AI实例
    print("\n2. 创建AI实例")
    success = ai_management_system.create_ai('test-ai-1', 'general', 'engineering')
    print(f"创建结果: {'成功' if success else '失败'}")

    # 测试培训AI实例
    print("\n3. 培训AI实例")
    success = ai_management_system.train_ai('test-ai-1')
    print(f"培训结果: {'成功' if success else '失败'}")

    # 测试部署AI实例
    print("\n4. 部署AI实例")
    success = ai_management_system.deploy_ai('test-ai-1', '分析代码性能问题')
    print(f"部署结果: {'成功' if success else '失败'}")

    # 等待一段时间
    print("\n5. 等待10秒，收集监控数据")
    time.sleep(10)

    # 测试获取AI实例状态
    print("\n6. 获取AI实例状态")
    status = ai_management_system.get_ai_status('test-ai-1')
    print(f"AI实例状态: {'获取成功' if status else '获取失败'}")
    if status:
        print(f"  状态: {status.get('status')}")
        print(f"  能力: {status.get('capability')}")
        print(f"  已培训: {status.get('trained')}")

    # 测试获取系统状态
    print("\n7. 获取系统状态")
    system_status = ai_management_system.get_system_status()
    print(f"系统状态: {'获取成功' if system_status else '获取失败'}")
    if system_status:
        print(f"  总实例数: {system_status.get('total_instances')}")
        print(f"  活跃实例数: {system_status.get('active_instances')}")
        print(f"  已培训实例数: {system_status.get('trained_instances')}")
        print(f"  监控实例数: {system_status.get('monitoring_instances')}")

    # 测试回收AI实例
    print("\n8. 回收AI实例")
    success = ai_management_system.recycle_ai('test-ai-1')
    print(f"回收结果: {'成功' if success else '失败'}")

    # 停止系统
    print("\n9. 停止AI管理系统")
    success = ai_management_system.stop()
    print(f"停止结果: {'成功' if success else '失败'}")

    print("\nAI管理系统测试完成")

if __name__ == '__main__':
    main()
