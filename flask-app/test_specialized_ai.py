#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试专业AI功能
"""

import sys
import os
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.ai_management_system import ai_management_system

def test_specialized_ai():
    """测试专业AI功能"""
    print("专业AI功能测试开始")
    
    # 启动系统
    print("\n1. 启动AI管理系统")
    success = ai_management_system.start()
    print(f"启动结果: {'成功' if success else '失败'}")
    
    # 测试创建数学教师AI
    print("\n2. 创建数学教师AI")
    success = ai_management_system.create_ai('math-teacher-ai-1', 'education', 'education_math')
    print(f"创建结果: {'成功' if success else '失败'}")
    
    # 测试创建语言教师AI
    print("\n3. 创建语言教师AI")
    success = ai_management_system.create_ai('language-teacher-ai-1', 'education', 'education_language')
    print(f"创建结果: {'成功' if success else '失败'}")
    
    # 测试创建科学教师AI
    print("\n4. 创建科学教师AI")
    success = ai_management_system.create_ai('science-teacher-ai-1', 'education', 'education_science')
    print(f"创建结果: {'成功' if success else '失败'}")
    
    # 测试创建历史教师AI
    print("\n5. 创建历史教师AI")
    success = ai_management_system.create_ai('history-teacher-ai-1', 'education', 'education_history')
    print(f"创建结果: {'成功' if success else '失败'}")
    
    # 测试创建艺术教师AI
    print("\n6. 创建艺术教师AI")
    success = ai_management_system.create_ai('art-teacher-ai-1', 'education', 'education_art')
    print(f"创建结果: {'成功' if success else '失败'}")
    
    # 测试培训数学教师AI
    print("\n7. 培训数学教师AI")
    success = ai_management_system.train_ai('math-teacher-ai-1')
    print(f"培训结果: {'成功' if success else '失败'}")
    
    # 测试部署数学教师AI
    print("\n8. 部署数学教师AI")
    success = ai_management_system.deploy_ai('math-teacher-ai-1', '生成数学题目和评估学生数学表现')
    print(f"部署结果: {'成功' if success else '失败'}")
    
    # 等待一段时间
    print("\n9. 等待10秒，收集监控数据")
    time.sleep(10)
    
    # 测试获取数学教师AI状态
    print("\n10. 获取数学教师AI状态")
    status = ai_management_system.get_ai_status('math-teacher-ai-1')
    print(f"AI实例状态: {'获取成功' if status else '获取失败'}")
    if status:
        print(f"  状态: {status.get('status')}")
        print(f"  能力: {status.get('capability')}")
        print(f"  已培训: {status.get('trained')}")
        print(f"  培训历史: {len(status.get('training_history', []))}")
    
    # 测试获取系统状态
    print("\n11. 获取系统状态")
    system_status = ai_management_system.get_system_status()
    print(f"系统状态: {'获取成功' if system_status else '失败'}")
    if system_status:
        print(f"  总实例数: {system_status.get('total_instances')}")
        print(f"  活跃实例数: {system_status.get('active_instances')}")
        print(f"  已培训实例数: {system_status.get('trained_instances')}")
        print(f"  监控实例数: {system_status.get('monitoring_instances')}")
    
    # 测试回收所有AI实例
    print("\n12. 回收所有AI实例")
    for ai_id in ['math-teacher-ai-1', 'language-teacher-ai-1', 'science-teacher-ai-1', 'history-teacher-ai-1', 'art-teacher-ai-1']:
        success = ai_management_system.recycle_ai(ai_id)
        print(f"回收 {ai_id}: {'成功' if success else '失败'}")
    
    # 停止系统
    print("\n13. 停止AI管理系统")
    success = ai_management_system.stop()
    print(f"停止结果: {'成功' if success else '失败'}")
    
    print("\n专业AI功能测试完成")

if __name__ == '__main__':
    test_specialized_ai()
