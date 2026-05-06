#!/usr/bin/env python3
"""
测试AI实验室功能

import sys
import os
import time

# 添加项目根目录到系统路径
sys.path.append('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app')

from app.ai.ai_lab import ai_lab

def test_ai_lab():
    """测试AI实验室功能"""
    print("=" * 50)
    print("测试AI实验室功能")
    print("=" * 50)
    # 1. 获取AI实验室状态
    print("1. 获取AI实验室状态:")
    status = ai_lab.get_status()
    print(f"   名称: {status['name']}")
    print(f"   版本: {status['version']}")
    print(f"   运行状态: {status['is_running']}")
    print(f"   组件状态: {status['component_status']}")
    print(f"   特征数量: {status['feature_count']}")

    # 2. 启动AI实验室
    print("\n2. 启动AI实验室:")
    result = ai_lab.start()
    print(f"   启动结果: {'成功' if result else '失败'}")

    # 等待1秒，让组件启动完成
    time.sleep(1)

    # 3. 再次获取AI实验室状态
    print("\n3. 再次获取AI实验室状态:")
    status = ai_lab.get_status()
    print(f"   运行状态: {status['is_running']}")

    print("\n4. 运行日志分析实验:")
        "log_analysis",
        {"log_content": "ERROR: 测试错误信息\nWARNING: 测试警告信息\nINFO: 测试信息日志"}
    )
    print(f"   实验结果: {'成功' if experiment_result['success'] else '失败'}")
    if experiment_result['success']:
        print(f"   日志分析结果: {experiment_result['result']}")

    # 5. 运行特征重要性实验
    print("\n5. 运行特征重要性实验:")
    experiment_result = ai_lab.run_experiment("feature_importance", {})
    print(f"   实验结果: {'成功' if experiment_result['success'] else '失败'}")
    if experiment_result['success']:
        print(f"   特征重要性: {experiment_result['result']}")

    # 6. 运行异常检测实验
    experiment_result = ai_lab.run_experiment("anomaly_detection", {})
    if experiment_result['success']:
        print(f"   异常数量: {len(experiment_result['result'])}")

    # 7. 运行系统优化
    optimize_result = ai_lab.optimize_system()
    print(f"   优化结果: {'成功' if optimize_result['success'] else '失败'}")
        print(f"   优化建议: {optimize_result['suggestions']}")

    # 8. 停止AI实验室
    print("\n8. 停止AI实验室:")
    result = ai_lab.stop()
    print(f"   停止结果: {'成功' if result else '失败'}")

    # 9. 再次获取AI实验室状态
    print("\n9. 再次获取AI实验室状态:")
    status = ai_lab.get_status()
    print(f"   运行状态: {status['is_running']}")

    print("\n" + "=" * 50)
    print("=" * 50)
if __name__ == "__main__":
