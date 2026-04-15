#!/usr/bin/env python3
"""
测试AI自动生成和任务分配功能
"""

import json
from ai_employee_system import get_ai_route_system

def test_ai_auto_generate():
    """测试AI自动生成功能"""
    print("=== 测试AI自动生成功能 ===")
    
    # 获取AI路由系统实例
    ai_route_system = get_ai_route_system()
    
    # 1. 测试AI级别信息
    print("\n1. 测试AI级别信息:")
    levels_result = ai_route_system.process_request("/ai/levels", {})
    print(json.dumps(levels_result, ensure_ascii=False, indent=2))
    assert levels_result["success"], "获取AI级别信息失败"
    assert "L1" in levels_result["levels"], "缺少L1级别"
    assert "L2" in levels_result["levels"], "缺少L2级别"
    assert "L3" in levels_result["levels"], "缺少L3级别"
    assert "L4" in levels_result["levels"], "缺少L4级别"
    print("✓ AI级别信息测试通过")
    
    # 2. 测试AI自动生成员工
    print("\n2. 测试AI自动生成员工:")
    generate_result = ai_route_system.process_request("/ai/generate", {})
    print(json.dumps(generate_result, ensure_ascii=False, indent=2))
    assert generate_result["success"], "自动生成AI员工失败"
    print(f"✓ AI自动生成员工测试通过，生成了{len(generate_result['generated_employees'])}个员工")
    
    # 3. 测试AI状态信息
    print("\n3. 测试AI状态信息:")
    status_result = ai_route_system.process_request("/ai/status", {})
    print(json.dumps(status_result, ensure_ascii=False, indent=2))
    assert "level_stats" in status_result, "缺少级别统计信息"
    assert "total_employees" in status_result, "缺少员工总数信息"
    assert "employee_types" in status_result, "缺少员工类型信息"
    print("✓ AI状态信息测试通过")
    
    # 4. 测试AI自动分配任务
    print("\n4. 测试AI自动分配任务:")
    allocate_result = ai_route_system.process_request("/ai/allocate", {})
    print(json.dumps(allocate_result, ensure_ascii=False, indent=2))
    assert allocate_result["success"], "自动分配任务失败"
    print("✓ AI自动分配任务测试通过")
    
    # 5. 测试系统状态
    print("\n5. 测试系统状态:")
    system_status = ai_route_system.get_status()
    print(json.dumps(system_status, ensure_ascii=False, indent=2))
    assert system_status["is_running"], "系统未运行"
    print(f"✓ 系统状态测试通过，当前系统运行中，共有{system_status['total_employees']}个AI员工")
    
    print("\n=== 所有测试通过 ===")

if __name__ == "__main__":
    test_ai_auto_generate()