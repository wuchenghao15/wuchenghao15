#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有专业AI功能
"""

import sys
import os
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.ai_management_system import ai_management_system

def test_all_specialized_ai():
    """测试所有专业AI功能"""
    print("所有专业AI功能测试开始")
    
    # 启动系统
    print("\n1. 启动AI管理系统")
    success = ai_management_system.start()
    print(f"启动结果: {'成功' if success else '失败'}")
    
    # 测试创建工程领域专业AI
    print("\n2. 测试创建工程领域专业AI")
    engineering_ais = [
        ('frontend-engineer-ai-1', 'engineering_frontend', '前端工程AI'),
        ('backend-engineer-ai-1', 'engineering_backend', '后端工程AI'),
        ('mobile-engineer-ai-1', 'engineering_mobile', '移动应用工程AI'),
        ('devops-engineer-ai-1', 'engineering_devops', 'DevOps工程AI')
    ]
    
    for ai_id, capability, name in engineering_ais:
        success = ai_management_system.create_ai(ai_id, 'engineering', capability)
        print(f"创建 {name}: {'成功' if success else '失败'}")
    
    # 测试创建网络领域专业AI
    print("\n3. 测试创建网络领域专业AI")
    network_ais = [
        ('network-security-ai-1', 'network_security', '网络安全AI'),
        ('network-operations-ai-1', 'network_operations', '网络运维AI'),
        ('network-architecture-ai-1', 'network_architecture', '网络架构AI')
    ]
    
    for ai_id, capability, name in network_ais:
        success = ai_management_system.create_ai(ai_id, 'network', capability)
        print(f"创建 {name}: {'成功' if success else '失败'}")
    
    # 测试创建设计领域专业AI
    print("\n4. 测试创建设计领域专业AI")
    design_ais = [
        ('ui-design-ai-1', 'design_ui', 'UI设计AI'),
        ('ux-design-ai-1', 'design_ux', 'UX设计AI'),
        ('graphic-design-ai-1', 'design_graphic', '平面设计AI'),
        ('product-design-ai-1', 'design_product', '产品设计AI')
    ]
    
    for ai_id, capability, name in design_ais:
        success = ai_management_system.create_ai(ai_id, 'design', capability)
        print(f"创建 {name}: {'成功' if success else '失败'}")
    
    # 测试创建用户行为领域专业AI
    print("\n5. 测试创建用户行为领域专业AI")
    user_behavior_ais = [
        ('behavior-analytics-ai-1', 'user_behavior_analytics', '用户行为分析AI'),
        ('user-profiling-ai-1', 'user_behavior_profiling', '用户画像AI'),
        ('recommendation-ai-1', 'user_behavior_recommendation', '推荐系统AI'),
        ('behavior-prediction-ai-1', 'user_behavior_prediction', '用户行为预测AI')
    ]
    
    for ai_id, capability, name in user_behavior_ais:
        success = ai_management_system.create_ai(ai_id, 'user_behavior', capability)
        print(f"创建 {name}: {'成功' if success else '失败'}")
    
    # 测试培训前端工程AI
    print("\n6. 测试培训前端工程AI")
    success = ai_management_system.train_ai('frontend-engineer-ai-1')
    print(f"培训前端工程AI: {'成功' if success else '失败'}")
    
    # 测试部署前端工程AI
    print("\n7. 测试部署前端工程AI")
    success = ai_management_system.deploy_ai('frontend-engineer-ai-1', '分析前端代码质量和安全性')
    print(f"部署前端工程AI: {'成功' if success else '失败'}")
    
    # 等待一段时间
    print("\n8. 等待10秒，收集监控数据")
    time.sleep(10)
    
    # 测试获取前端工程AI状态
    print("\n9. 测试获取前端工程AI状态")
    status = ai_management_system.get_ai_status('frontend-engineer-ai-1')
    print(f"AI实例状态: {'获取成功' if status else '获取失败'}")
    if status:
        print(f"  状态: {status.get('status')}")
        print(f"  能力: {status.get('capability')}")
        print(f"  已培训: {status.get('trained')}")
        print(f"  培训历史: {len(status.get('training_history', []))}")
    
    # 测试获取系统状态
    print("\n10. 测试获取系统状态")
    system_status = ai_management_system.get_system_status()
    print(f"系统状态: {'获取成功' if system_status else '失败'}")
    if system_status:
        print(f"  总实例数: {system_status.get('total_instances')}")
        print(f"  活跃实例数: {system_status.get('active_instances')}")
        print(f"  已培训实例数: {system_status.get('trained_instances')}")
        print(f"  监控实例数: {system_status.get('monitoring_instances')}")
    
    # 测试回收所有AI实例
    print("\n11. 测试回收所有AI实例")
    all_ais = [
        'frontend-engineer-ai-1', 'backend-engineer-ai-1', 'mobile-engineer-ai-1', 'devops-engineer-ai-1',
        'network-security-ai-1', 'network-operations-ai-1', 'network-architecture-ai-1',
        'ui-design-ai-1', 'ux-design-ai-1', 'graphic-design-ai-1', 'product-design-ai-1',
        'behavior-analytics-ai-1', 'user-profiling-ai-1', 'recommendation-ai-1', 'behavior-prediction-ai-1'
    ]
    
    for ai_id in all_ais:
        success = ai_management_system.recycle_ai(ai_id)
        print(f"回收 {ai_id}: {'成功' if success else '失败'}")
    
    # 停止系统
    print("\n12. 停止AI管理系统")
    success = ai_management_system.stop()
    print(f"停止结果: {'成功' if success else '失败'}")
    
    print("\n所有专业AI功能测试完成")

if __name__ == '__main__':
    test_all_specialized_ai()
