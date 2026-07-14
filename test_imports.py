#!/usr/bin/env python3
"""测试各个模块的导入"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import(name, module_path):
    print(f"测试导入 {name}...", flush=True)
    try:
        __import__(module_path)
        print(f"  ✓ {name} 导入成功", flush=True)
        return True
    except Exception as e:
        print(f"  ✗ {name} 导入失败: {e}", flush=True)
        return False

print("=" * 50, flush=True)
print("测试模块导入", flush=True)
print("=" * 50, flush=True)

test_import("ai_employees", "ai_engines.ai_employees")
test_import("ai_employee_auto_generator", "ai_engines.ai_employee_auto_generator")
test_import("version_agent_ai", "ai_engines.version_agent_ai")
test_import("automation_plan_agent", "ai_engines.automation_plan_agent")

print("\n所有测试完成!", flush=True)
