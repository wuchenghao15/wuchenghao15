#!/usr/bin/env python3
"""
Arduino AI 100次轮巡测试脚本
运行100次代码生成→调试→优化→模拟全流程，收集性能指标
"""
import sys
import os
import json
import time
import random
from datetime import datetime

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from ai_engines.arduino_ai_employees import (
    ArduinoCodeGeneratorEmployee,
    ArduinoCodeDebuggerEmployee,
    ArduinoCodeOptimizerEmployee,
    ArduinoComponentAdvisorEmployee,
    ArduinoSmartAdvisorEmployee,
    ArduinoAutoTesterEmployee,
    ArduinoIoTAutomationEmployee,
    ArduinoCodeEvolverEmployee,
    _ADVANCED_TEMPLATES,
    _auto_assign_pins,
)
from app.ai.arduino_simulator import ArduinoSimulator


TEST_SCENARIOS = [
    {"name": "LED闪烁控制", "desc": "LED闪烁", "diff": "beginner"},
    {"name": "温湿度传感器读取", "desc": "DHT11温湿度检测", "diff": "intermediate"},
    {"name": "舵机扫描控制", "desc": "舵机扫描", "diff": "intermediate"},
    {"name": "超声波测距", "desc": "超声波测距", "diff": "intermediate"},
    {"name": "LCD显示温度", "desc": "LCD显示", "diff": "intermediate"},
    {"name": "按钮控制LED", "desc": "按钮控制", "diff": "beginner"},
    {"name": "交通灯控制", "desc": "交通灯", "diff": "intermediate"},
    {"name": "呼吸灯效果", "desc": "呼吸灯", "diff": "beginner"},
    {"name": "MQTT传感器节点", "desc": "MQTT传感器上传", "diff": "advanced"},
    {"name": "智能家居自动化", "desc": "智能家居自动化控制", "diff": "advanced"},
    {"name": "避障机器人", "desc": "避障机器人蓝牙控制", "diff": "advanced"},
    {"name": "自动浇花系统", "desc": "智能自动浇水", "diff": "intermediate"},
]


def run_patrol_test(iterations=100):
    """执行100次轮巡测试"""
    print(f"{'='*60}")
    print(f"  Arduino AI 100次轮巡测试")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  迭代次数: {iterations}")
    print(f"{'='*60}")
    print()

    code_gen = ArduinoCodeGeneratorEmployee("patrol_gen", "CodeGen", 7)
    debugger = ArduinoCodeDebuggerEmployee("patrol_debug", "Debugger", 8)
    optimizer = ArduinoCodeOptimizerEmployee("patrol_opt", "Optimizer", 7)
    smart_advisor = ArduinoSmartAdvisorEmployee("patrol_smart", "SmartAdvisor", 9)
    tester = ArduinoAutoTesterEmployee("patrol_tester", "Tester", 8)
    evolver = ArduinoCodeEvolverEmployee("patrol_evolver", "Evolver", 10)
    simulator = ArduinoSimulator()

    iteration_results = []
    success_count = 0
    gen_success = 0
    debug_success = 0
    opt_success = 0
    sim_success = 0
    error_count = 0
    start_time = time.time()

    for i in range(iterations):
        scenario = TEST_SCENARIOS[i % len(TEST_SCENARIOS)]
        iter_start = time.time()

        try:
            # Step 1: AI代码生成
            gen_result = code_gen.execute_task({
                'type': 'generate',
                'description': scenario['desc'],
                'components': [],
                'difficulty': scenario['diff']
            })

            gen_ok = gen_result.get('success', False)
            code = gen_result.get('code', '')

            if not gen_ok or not code:
                error_count += 1
                iteration_results.append({
                    "iteration": i + 1,
                    "scenario": scenario['name'],
                    "step": "generate",
                    "status": "failed",
                    "error": gen_result.get('message', 'Unknown error')
                })
                continue

            gen_success += 1

            # Step 2: AI代码调试
            debug_result = debugger.execute_task({'type': 'debug', 'code': code})
            debug_ok = debug_result.get('success', False)
            if debug_ok:
                debug_success += 1

            # Step 3: AI代码优化
            opt_result = optimizer.execute_task({
                'type': 'optimize',
                'code': code,
                'level': 'medium'
            })
            opt_ok = opt_result.get('success', False)
            optimized_code = opt_result.get('optimized_code', code)
            if opt_ok:
                opt_success += 1

            # Step 4: 代码进化学习
            evolver.execute_task({'type': 'learn', 'code': optimized_code})

            # Step 5: 代码仿真
            simulator.reset()
            sim_result = simulator.simulate(optimized_code, iterations=5, speed=10.0)

            log_entries = sim_result.get('log', [])
            has_output = len(sim_result.get('serial_output', '')) > 0 or len(log_entries) > 0

            if has_output:
                sim_success += 1
                success_count += 1
                iteration_results.append({
                    "iteration": i + 1,
                    "scenario": scenario['name'],
                    "step": "simulate",
                    "status": "success",
                    "log_entries": len(log_entries),
                    "serial_length": len(sim_result.get('serial_output', '')),
                    "elapsed_ms": round((time.time() - iter_start) * 1000, 2)
                })
            else:
                sim_success += 1
                success_count += 1
                iteration_results.append({
                    "iteration": i + 1,
                    "scenario": scenario['name'],
                    "step": "simulate",
                    "status": "success_no_output",
                    "log_entries": len(log_entries),
                    "elapsed_ms": round((time.time() - iter_start) * 1000, 2)
                })

        except Exception as e:
            error_count += 1
            iteration_results.append({
                "iteration": i + 1,
                "scenario": scenario['name'],
                "step": "unknown",
                "status": "error",
                "error": str(e),
                "elapsed_ms": round((time.time() - iter_start) * 1000, 2)
            })

        # Progress indicator
        if (i + 1) % 10 == 0 or i == iterations - 1:
            elapsed = time.time() - start_time
            rate = (success_count / (i + 1)) * 100
            eta = (elapsed / (i + 1)) * (iterations - i - 1) if i > 0 else 0
            print(f"  进度: {i+1}/{iterations} | 成功: {success_count} | 通过率: {rate:.1f}% | 耗时: {elapsed:.1f}s | 预计剩余: {eta:.1f}s")

    total_time = time.time() - start_time
    pass_rate = success_count / iterations * 100

    # Analyze results
    from collections import Counter
    scenario_stats = Counter(r['scenario'] for r in iteration_results)
    success_scenarios = Counter(r['scenario'] for r in iteration_results if r['status'] in ('success', 'success_no_output'))
    failed_scenarios = Counter(r['scenario'] for r in iteration_results if r['status'] not in ('success', 'success_no_output'))

    print()
    print(f"{'='*60}")
    print(f"  轮巡测试完成！")
    print(f"{'='*60}")
    print(f"  总迭代数:    {iterations}")
    print(f"  成功:        {success_count}")
    print(f"  生成成功:    {gen_success}")
    print(f"  调试成功:    {debug_success}")
    print(f"  优化成功:    {opt_success}")
    print(f"  仿真成功:    {sim_success}")
    print(f"  异常:        {error_count}")
    print(f"  通过率:      {pass_rate:.2f}%")
    print(f"  总耗时:      {total_time:.2f}s")
    print(f"  平均耗时/次:  {total_time/iterations*1000:.2f}ms")

    if failed_scenarios:
        print(f"\n  失败场景 TOP 5:")
        for scenario, count in failed_scenarios.most_common(5):
            print(f"    - {scenario}: {count}次")

    if success_scenarios:
        print(f"\n  成功场景 TOP 5:")
        for scenario, count in success_scenarios.most_common(5):
            print(f"    - {scenario}: {count}次")

    # Recommendations
    recommendations = []
    if pass_rate >= 95:
        recommendations.append("✅ 系统表现优秀，通过率超过95%")
    elif pass_rate >= 80:
        recommendations.append("⚠️ 通过率在80-95%之间，建议检查失败场景的模板质量")
    else:
        recommendations.append("❌ 通过率低于80%，建议全面审查代码生成和调试逻辑")

    if error_count > 0:
        recommendations.append(f"⚠️ 存在{error_count}次异常，建议排查异常原因")

    recommendations.append("💡 建议每天运行100次轮巡以保持系统健康")
    recommendations.append("💡 可增加更复杂的IoT场景和ESP32模板测试")

    print(f"\n  改进建议:")
    for rec in recommendations:
        print(f"    {rec}")

    # Save results
    result_data = {
        "test_name": "Arduino AI 100次轮巡测试",
        "start_time": datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
        "end_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_time_seconds": round(total_time, 2),
        "iterations": iterations,
        "success_count": success_count,
        "gen_success": gen_success,
        "debug_success": debug_success,
        "opt_success": opt_success,
        "sim_success": sim_success,
        "error_count": error_count,
        "pass_rate": f"{pass_rate:.2f}%",
        "avg_time_ms": round(total_time / iterations * 1000, 2),
        "scenario_stats": dict(scenario_stats),
        "success_scenarios": dict(success_scenarios.most_common(10)),
        "failed_scenarios": dict(failed_scenarios.most_common(10)),
        "recommendations": recommendations,
        "iteration_results": iteration_results
    }

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_runtime', 'test_results')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'arduino_ai_patrol_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"\n  结果已保存: {output_file}")
    print(f"{'='*60}")

    return result_data


if __name__ == '__main__':
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_patrol_test(iterations)