#!/usr/bin/env python3
"""
创建诊断AI员工，用于处理服务器启动和访问问题
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

print("创建诊断AI员工...")

# 导入AI实例管理器
try:
    from app.ai.instances import ai_instance_manager
    print("✓ 成功导入AI实例管理器")
    
    # 检查是否已存在诊断AI实例
    diagnostic_ai_id = "diagnostic-ai-001"
    existing_instance = ai_instance_manager.get_ai_instance(diagnostic_ai_id)
    
    if existing_instance:
        print(f"✓ 诊断AI员工 {diagnostic_ai_id} 已存在")
        ai_instance = existing_instance
    else:
        # 创建诊断AI实例
        print("创建新的诊断AI员工...")
        ai_instance = ai_instance_manager.create_ai_instance(
            instance_id=diagnostic_ai_id,
            ai_type="technical",
            name="系统诊断AI",
            description="负责处理服务器启动和访问问题，记录问题特征和解决思路到AI脑库",
            functions=["问题诊断", "服务器启动分析", "端口占用检测", "路由配置检查", "日志分析", "问题记录", "解决方案生成", "AI脑库更新"],
            responsibilities=["分析服务器启动失败原因", "检测端口占用情况", "检查路由配置", "分析日志文件", "记录问题特征", "生成解决方案", "更新AI脑库"],
            config={
                "version": 1.2,
                "diagnostic_tools": ["端口检测", "路由检查", "日志分析", "进程监控"],
                "auto_fix": True,
                "reporting": True,
                "log_analysis": {
                    "enabled": True,
                    "log_paths": ["app.log", "error.log"],
                    "alert_threshold": 5
                },
                "brain_database": {
                    "enabled": True,
                    "upload_interval": 60,
                    "retention_days": 30
                }
            }
        )
        print(f"✓ 成功创建诊断AI员工: {diagnostic_ai_id}")
    
    # 记录当前服务器启动问题
    print("\n记录当前服务器启动问题...")
    
    # 问题描述
    problem_description = "服务器无法在端口8888或8080上启动，curl请求返回连接失败"
    
    # 问题特征
    problem_features = [
        "服务器启动日志显示正常，但无法建立连接",
        "curl请求返回: curl: (7) Failed to connect to localhost port 8888 after 0 ms: Couldn't connect to server",
        "端口8888和8080似乎未被占用",
        "服务器启动脚本没有报错",
        "视图函数测试正常"
    ]
    
    # 解决思路
    solution_ideas = [
        "检查服务器绑定的IP地址，确保绑定到127.0.0.1或0.0.0.0",
        "检查防火墙设置，确保端口8888和8080未被阻止",
        "检查服务器启动脚本，确保正确调用run_simple或app.run",
        "检查应用配置，确保DEBUG模式正确设置",
        "尝试使用不同的端口启动服务器",
        "检查Werkzeug版本，确保与Flask版本兼容"
    ]
    
    # 记录问题到日志
    from app.utils.logging import logger
    logger.info(f"诊断AI员工记录问题: {problem_description}")
    logger.info(f"问题特征: {', '.join(problem_features)}")
    logger.info(f"解决思路: {', '.join(solution_ideas)}")
    
    print("\n✓ 成功记录服务器启动问题到日志")
    print("\n诊断AI员工已创建并配置完成，将继续监控和解决服务器启动问题")
    
    # 显示AI实例信息
    print(f"\n诊断AI员工信息:")
    print(f"  ID: {ai_instance['instance_id']}")
    print(f"  名称: {ai_instance['name']}")
    print(f"  类型: {ai_instance['ai_type']}")
    print(f"  状态: {ai_instance['status']}")
    print(f"  功能: {', '.join(ai_instance['functions'])}")
    
except Exception as e:
    print(f"✗ 创建诊断AI员工失败: {str(e)}")
    import traceback
    traceback.print_exc()