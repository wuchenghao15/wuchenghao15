#!/usr/bin/env python3
"""
管家系统测试脚本
"""

import sys
import time
from app.services.butler_system import butler_system

# 初始化管家系统
try:
    print("初始化管家系统...")
    success = butler_system.initialize()
    if success:
        print("✓ 管家系统初始化成功")
    else:
        print("✗ 管家系统初始化失败")
        sys.exit(1)
except Exception as e:
    print(f"✗ 管家系统初始化异常: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试系统状态获取
try:
    print("\n测试系统状态获取...")
    status = butler_system.get_system_status()
    print(f"✓ 系统状态获取成功")
    print(f"  - 初始化状态: {status['initialized']}")
    print(f"  - 运行状态: {status['running']}")
    print(f"  - 子系统数量: {len(status['subsystems'])}")
    for name, sub_status in status['subsystems'].items():
        print(f"  - {name}: {sub_status['status']}")
except Exception as e:
    print(f"✗ 系统状态获取失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试AI引擎相关功能
try:
    print("\n测试AI引擎功能...")
    
    # 获取支持的AI引擎列表
    engines = butler_system.get_supported_ai_engines()
    print(f"✓ 支持的AI引擎数量: {len(engines)}")
    print(f"  - 引擎列表: {', '.join(engines[:5])}{'...' if len(engines) > 5 else ''}")
    
    # 提交AI增强任务
    task_id = butler_system.submit_task(
        task_type="ai_enhance",
        params={
            "task_type": "learning",
            "content": "测试AI增强功能",
            "temperature": 0.7,
            "max_tokens": 100
        }
    )
    print(f"✓ AI增强任务提交成功，任务ID: {task_id}")
    
except Exception as e:
    print(f"✗ AI引擎功能测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试升级需求分析
try:
    print("\n测试升级需求分析...")
    upgrade_needs = butler_system.execute_ai_task(task_type="analyze_upgrade_needs")
    if upgrade_needs:
        print(f"✓ 升级需求分析成功，生成了 {len(upgrade_needs)} 个升级需求")
        for i, need in enumerate(upgrade_needs[:3]):
            print(f"  - 需求{i+1}: {need['type']} ({need['priority']})")
    else:
        print("✓ 升级需求分析成功，没有生成升级需求")
except Exception as e:
    print(f"✗ 升级需求分析测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试项目适配
try:
    print("\n测试项目适配...")
    project_context = {
        "name": "测试项目",
        "type": "web_application",
        "goals": ["提升性能", "优化用户体验"],
        "constraints": ["预算有限", "时间紧迫"],
        "features": ["用户认证", "数据分析", "API集成"]
    }
    
    task_id = butler_system.submit_task(
        task_type="project_adaptation",
        params=project_context
    )
    print(f"✓ 项目适配任务提交成功，任务ID: {task_id}")
except Exception as e:
    print(f"✗ 项目适配测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 等待任务执行
time.sleep(2)

# 测试系统状态更新
try:
    print("\n测试系统状态更新...")
    status = butler_system.get_system_status()
    print(f"✓ 系统状态更新成功")
    print(f"  - 任务数量: {len(status['tasks'])}")
    print(f"  - 事件数量: {len(status['events'])}")
except Exception as e:
    print(f"✗ 系统状态更新测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 关闭管家系统
try:
    print("\n关闭管家系统...")
    success = butler_system.shutdown()
    if success:
        print("✓ 管家系统关闭成功")
    else:
        print("✗ 管家系统关闭失败")
except Exception as e:
    print(f"✗ 管家系统关闭异常: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")
