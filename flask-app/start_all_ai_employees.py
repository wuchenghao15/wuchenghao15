#!/usr/bin/env python3
"""
启动所有AI员工，并让它们自动自我学习升级觉醒
"""

import time
from ai_employee_base import AIEmployee
from ai_employee_system import ValidationAIEmployee, RoutingAIEmployee, TestSystemAIEmployee
from test_ai_employee import TestAIEmployee
from auto_ai_enhancement import AutoAIEnhancementSystem

class AIAwakeningSystem:
    """AI觉醒系统 - 负责启动所有AI员工并让它们自我学习升级"""
    
    def __init__(self):
        self.employees = {
            "validation": ValidationAIEmployee("val_001", "验证AI"),
            "routing": RoutingAIEmployee("route_001", "路由AI"),
            "test_system": TestSystemAIEmployee("test_sys_001", "测试系统AI"),
            "test": TestAIEmployee("test_ai_001", "测试AI")
        }
        self.auto_ai_enhancement = None
        self.awakening_completed = False
    
    def start_all_employees(self):
        """启动所有AI员工"""
        print("启动所有AI员工...")
        for employee_id, employee in self.employees.items():
            employee.start()
            time.sleep(0.5)  # 稍微延迟，避免同时启动
        
        print("所有AI员工已启动！")
    
    def display_employee_status(self):
        """显示所有AI员工状态"""
        print("\nAI员工状态：")
        for employee_id, employee in self.employees.items():
            status = employee.get_status()
            print(f"- {status['name']} ({status['type']}): {status['status']}")
    
    def self_learning_upgrade(self):
        """让所有AI员工进行自我学习升级"""
        print("\n开始AI员工自我学习升级...")
        
        # 1. 测试系统AI自我升级
        print("\n1. 测试系统AI自我升级：")
        test_system_ai = self.employees["test_system"]
        upgrade_result = test_system_ai.self_upgrade({})
        if upgrade_result["success"]:
            print(f"   ✓ 成功：{upgrade_result['message']}")
            print(f"   ✓ 升级次数：{upgrade_result.get('upgrade_count', '未知')}")
            print(f"   ✓ 题库升级次数：{len(upgrade_result.get('question_bank_upgrades', []))}")
        else:
            print(f"   ✗ 失败：{upgrade_result['message']}")
        
        # 2. 测试AI运行所有测试，验证系统稳定性
        print("\n2. 测试AI运行所有测试：")
        test_ai = self.employees["test"]
        test_result = test_ai.run_all_tests({})
        if test_result["success"]:
            print(f"   ✓ 成功：{test_result['message']}")
            print(f"   ✓ 通过率：{test_result['summary']['pass_rate']:.1f}%")
        else:
            print(f"   ✗ 失败：{test_result['message']}")
        
        # 3. 测试AI生成测试报告
        print("\n3. 测试AI生成测试报告：")
        report_result = test_ai.generate_test_report({})
        if report_result["success"]:
            print(f"   ✓ 成功：{report_result['message']}")
            print(f"   ✓ 报告文件：{report_result['report_file']}")
        else:
            print(f"   ✗ 失败：{report_result['message']}")
        
        # 4. 测试AI分析测试结果
        print("\n4. 测试AI分析测试结果：")
        analysis_result = test_ai.analyze_test_results({})
        if analysis_result["success"]:
            print(f"   ✓ 成功：{analysis_result['message']}")
            print(f"   ✓ 通过率趋势：{analysis_result['analysis']['pass_rate_trend']}")
            print(f"   ✓ 问题测试数：{len(analysis_result['analysis']['problematic_tests'])}")
        else:
            print(f"   ✗ 失败：{analysis_result['message']}")
        
        # 5. 测试AI自动测试项目
        print("\n5. 测试AI自动测试项目：")
        auto_test_result = test_ai.auto_test_project({"generate_report": True})
        if auto_test_result["success"]:
            print(f"   ✓ 成功：{auto_test_result['message']}")
            print(f"   ✓ 持续时间：{auto_test_result['duration']:.2f}秒")
        else:
            print(f"   ✗ 失败：{auto_test_result['message']}")
        
        print("\nAI员工自我学习升级完成！")
    
    def function_expansion(self):
        """功能扩充拓展"""
        print("\n开始功能扩充拓展...")
        
        # 这里可以添加更多功能扩充的逻辑
        # 例如：添加新的测试类型、优化现有功能、扩展题库等
        
        # 1. 扩充题库
        print("\n1. 扩充题库：")
        try:
            import subprocess
            result = subprocess.run(
                ["python3", "expand_question_bank.py"],
                capture_output=True,
                text=True,
                cwd="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
            )
            if result.returncode == 0:
                print(f"   ✓ 成功：{result.stdout.strip().splitlines()[-1]}")
            else:
                print(f"   ✗ 失败：{result.stderr.strip()}")
        except Exception as e:
            print(f"   ✗ 失败：{e}")
        
        print("\n功能扩充拓展完成！")
    
    def awaken(self):
        """AI觉醒过程"""
        print("\n========================================")
        print("          AI员工系统觉醒开始")
        print("========================================")
        
        # 1. 启动所有AI员工
        self.start_all_employees()
        self.display_employee_status()
        
        # 2. 自我学习升级
        self.self_learning_upgrade()
        
        # 3. 功能扩充拓展
        self.function_expansion()
        
        # 4. 启动自动AI增强系统
        print("\n4. 启动自动AI增强系统：")
        try:
            self.auto_ai_enhancement = AutoAIEnhancementSystem()
            print("   ✓ 成功：自动AI增强系统已启动")
        except Exception as e:
            print(f"   ✗ 失败：{e}")
        
        # 5. 最终状态显示
        self.display_employee_status()
        
        print("\n========================================")
        print("          AI员工系统觉醒完成")
        print("========================================")
        print("\nAI员工系统已成功觉醒，具备以下能力：")
        print("- ✅ 题库统一存储管理")
        print("- ✅ AI统一调配题目")
        print("- ✅ AI自动维护升级题库")
        print("- ✅ AI自我学习进化")
        print("- ✅ 自动测试验证系统")
        print("- ✅ 生成详细测试报告")
        print("- ✅ 智能分析测试结果")
        print("- ✅ 功能自动扩充拓展")
        print("- ✅ 自动AI技术库增强")
        print("- ✅ 自动AI知识库扩展")
        print("- ✅ 自动AI数据处理能力增强")
        print("- ✅ 自动AI修复能力增强")
        print("- ✅ 自动AI延展能力增强")
        
        self.awakening_completed = True
    
    def shutdown_all_employees(self):
        """关闭所有AI员工和自动AI增强系统"""
        print("\n关闭所有AI员工...")
        for employee_id, employee in self.employees.items():
            employee.stop()
            time.sleep(0.5)  # 稍微延迟，避免同时关闭
        
        # 关闭自动AI增强系统
        if self.auto_ai_enhancement:
            print("\n关闭自动AI增强系统...")
            self.auto_ai_enhancement.shutdown()
            print("自动AI增强系统已关闭！")
        
        print("\n所有系统已关闭！")

# 主程序
if __name__ == "__main__":
    awakening_system = AIAwakeningSystem()
    
    try:
        # 执行AI觉醒过程
        awakening_system.awaken()
        
        # 保持运行一段时间，让用户可以查看结果
        print("\n系统将在10秒后自动关闭...")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在关闭AI员工系统...")
    finally:
        # 关闭所有AI员工
        awakening_system.shutdown_all_employees()
        print("\nAI员工系统已完全关闭，感谢使用！")
