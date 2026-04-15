#!/usr/bin/env python3
"""
测试AI自动化管理系统
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_auto_management import get_ai_auto_management

def test_ai_auto_management():
    """测试AI自动化管理系统"""
    print("\n=== 开始测试AI自动化管理系统 ===\n")
    
    # 创建AI自动化管理系统实例
    print("1. 创建AI自动化管理系统实例...")
    ai_auto_management = get_ai_auto_management()
    print("✓ AI自动化管理系统实例创建成功")
    
    # 测试启动AI自动化管理系统
    print("\n2. 启动AI自动化管理系统...")
    ai_auto_management.start()
    print("✓ AI自动化管理系统启动成功")
    
    # 等待一段时间，让系统运行
    print("\n3. 系统运行中... (等待10秒)")
    time.sleep(10)
    
    # 测试获取系统概览
    print("\n4. 获取系统概览...")
    overview = ai_auto_management.get_system_overview()
    print(f"✓ 系统概览获取成功: {json.dumps(overview, ensure_ascii=False, indent=2)}")
    
    # 测试获取优化建议
    print("\n5. 获取优化建议...")
    suggestions = ai_auto_management.get_optimization_suggestions()
    print(f"✓ 优化建议获取成功: {json.dumps(suggestions, ensure_ascii=False, indent=2)}")
    
    # 测试停止AI自动化管理系统
    print("\n6. 停止AI自动化管理系统...")
    ai_auto_management.stop()
    print("✓ AI自动化管理系统停止成功")
    
    print("\n=== AI自动化管理系统测试完成 ===\n")
    return True

def test_ai_auto_management_integration():
    """测试AI自动化管理系统与其他AI组件的集成"""
    print("\n=== 开始测试AI自动化管理系统集成 ===\n")
    
    # 导入其他AI组件
    from ai_self_improvement import get_ai_self_improvement
    from ai_brain import get_ai_brain
    from ai_log_analyzer import get_log_analyzer
    from ai_anomaly_detector import get_ai_detector
    
    # 创建AI自动化管理系统实例
    print("1. 创建AI自动化管理系统实例...")
    ai_auto_management = get_ai_auto_management()
    print("✓ AI自动化管理系统实例创建成功")
    
    # 检查AI组件是否能正常访问
    print("\n2. 检查AI组件访问...")
    
    print("   - 检查AI自我提升系统...")
    ai_self_improvement = get_ai_self_improvement()
    print("     ✓ AI自我提升系统访问成功")
    
    print("   - 检查AI大脑...")
    ai_brain = get_ai_brain()
    print("     ✓ AI大脑访问成功")
    
    print("   - 检查日志分析器...")
    log_analyzer = get_log_analyzer()
    print("     ✓ 日志分析器访问成功")
    
    print("   - 检查异常检测器...")
    ai_anomaly_detector = get_ai_detector()
    print("     ✓ 异常检测器访问成功")
    
    print("✓ 所有AI组件访问成功")
    
    print("\n=== AI自动化管理系统集成测试完成 ===\n")
    return True

if __name__ == '__main__':
    print("MTSCOS AI自动化管理系统测试")
    print(f"测试时间: {datetime.now().isoformat()}")
    
    # 运行测试
    try:
        test_ai_auto_management()
        test_ai_auto_management_integration()
        print("\n🎉 所有测试通过！AI自动化管理系统工作正常。")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
