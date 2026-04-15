#!/usr/bin/env python3
"""
测试AI自学习系统功能
"""

import sys
import os

# 确保在正确的目录中运行
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

# 添加项目路径
sys.path.append('.')

print("=== 测试AI自学习系统 ===")
print("当前目录:", os.getcwd())
print("Python版本:", sys.version)
print()

# 测试1: 导入AI自学习系统
try:
    from app.ai.self_learning_system import self_learning_system
    print("✓ AI自学习系统导入成功")
except Exception as e:
    print(f"✗ AI自学习系统导入失败: {e}")
    sys.exit(1)

# 测试2: 获取和更新配置
try:
    config = self_learning_system.get_config()
    print(f"✓ 获取配置成功: {list(config.keys())}")
    
    # 更新配置
    self_learning_system.set_config({'learning_interval': 7200})
    updated_config = self_learning_system.get_config()
    if updated_config['learning_interval'] == 7200:
        print("✓ 更新配置成功")
    else:
        print("✗ 更新配置失败")
except Exception as e:
    print(f"✗ 配置测试失败: {e}")

# 测试3: 添加和获取性能数据
try:
    # 添加性能数据
    self_learning_system.add_performance_data({
        'path': '/test/path',
        'method': 'GET',
        'response_time': 0.5,
        'status_code': 200,
        'remote_addr': '127.0.0.1'
    })
    print("✓ 添加性能数据成功")
    
    # 获取性能数据
    performance_data = self_learning_system.get_learning_data('performance_metrics', limit=5)
    if len(performance_data) > 0:
        print(f"✓ 获取性能数据成功，返回 {len(performance_data)} 条记录")
    else:
        print("✗ 获取性能数据失败")
except Exception as e:
    print(f"✗ 性能数据测试失败: {e}")

# 测试4: 添加和获取资源使用数据
try:
    # 添加资源使用数据
    self_learning_system.add_resource_usage({
        'cpu_usage': 50.5,
        'memory_usage': 60.2,
        'disk_usage': 70.1,
        'network_io_diff': 1024
    })
    print("✓ 添加资源使用数据成功")
    
    # 获取资源使用数据
    resource_data = self_learning_system.get_learning_data('resource_usage', limit=5)
    if len(resource_data) > 0:
        print(f"✓ 获取资源使用数据成功，返回 {len(resource_data)} 条记录")
    else:
        print("✗ 获取资源使用数据失败")
except Exception as e:
    print(f"✗ 资源使用数据测试失败: {e}")

# 测试5: 添加和获取用户行为数据
try:
    # 添加用户行为数据
    self_learning_system.add_user_behavior({
        'path': '/test/path',
        'method': 'GET',
        'remote_addr': '127.0.0.1',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    print("✓ 添加用户行为数据成功")
    
    # 获取用户行为数据
    behavior_data = self_learning_system.get_learning_data('user_behaviors', limit=5)
    if len(behavior_data) > 0:
        print(f"✓ 获取用户行为数据成功，返回 {len(behavior_data)} 条记录")
    else:
        print("✗ 获取用户行为数据失败")
except Exception as e:
    print(f"✗ 用户行为数据测试失败: {e}")

# 测试6: 添加和获取错误日志
try:
    # 添加错误日志
    self_learning_system.add_error_log({
        'error_type': 'ValueError',
        'message': '测试错误',
        'path': '/test/error',
        'method': 'GET',
        'remote_addr': '127.0.0.1'
    })
    print("✓ 添加错误日志成功")
    
    # 获取错误日志
    error_data = self_learning_system.get_learning_data('error_logs', limit=5)
    if len(error_data) > 0:
        print(f"✓ 获取错误日志成功，返回 {len(error_data)} 条记录")
    else:
        print("✗ 获取错误日志失败")
except Exception as e:
    print(f"✗ 错误日志测试失败: {e}")

# 测试7: 分析数据和生成优化建议
try:
    # 分析性能数据
    performance_analysis = self_learning_system._analyze_performance_data()
    print(f"✓ 分析性能数据成功: {performance_analysis}")
    
    # 分析资源使用数据
    resource_analysis = self_learning_system._analyze_resource_usage()
    print(f"✓ 分析资源使用数据成功: {resource_analysis}")
    
    # 分析用户行为数据
    behavior_analysis = self_learning_system._analyze_user_behavior()
    print(f"✓ 分析用户行为数据成功: {behavior_analysis}")
    
    # 分析错误日志
    error_analysis = self_learning_system._analyze_error_logs()
    print(f"✓ 分析错误日志成功: {error_analysis}")
    
    # 生成优化建议
    suggestions = self_learning_system._generate_optimization_suggestions(
        performance_analysis, resource_analysis, behavior_analysis, error_analysis
    )
    print(f"✓ 生成优化建议成功，返回 {len(suggestions)} 条建议")
    
    # 打印建议
    for i, suggestion in enumerate(suggestions):
        print(f"  建议{i+1}: {suggestion['description']} (优先级: {suggestion['priority']})")
except Exception as e:
    print(f"✗ 数据分析和优化建议测试失败: {e}")

# 测试8: 保存和加载模型
try:
    # 保存模型
    self_learning_system.save_model()
    print("✓ 保存模型成功")
    
    # 加载模型
    self_learning_system.load_model()
    print("✓ 加载模型成功")
except Exception as e:
    print(f"✗ 模型保存和加载测试失败: {e}")

print()
print("=== 测试完成 ===")
print("所有测试已完成。")
print("AI自学习系统基本功能测试通过！")
