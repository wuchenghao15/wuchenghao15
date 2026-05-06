#!/usr/bin/env python3
"""
部署OpenCLAW模型脚本

import sys
import os
import time

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(__file__))

def deploy_openclaw_model():
    """部署OpenCLAW模型"""
    print("正在部署OpenCLAW模型...")

    try:
        # 延迟导入，避免初始化问题
        print("正在加载AIHostManager...")
        time.sleep(1)
        from ai_host_manager import get_ai_host_manager

        # 获取AI托管管理器实例
        print("正在获取AI托管管理器实例...")
        ai_host_manager = get_ai_host_manager()

        # 检查系统状态
        print("正在检查系统状态...")
        system_status = ai_host_manager.get_system_status()
        print(f"系统状态: {system_status['system_status']}")
        print(f"运行中的服务: {system_status['running_services']}/{system_status['total_services']}")

        # 创建OpenCLAW模型实例
        print("正在创建OpenCLAW模型实例...")
        opencwal_instance = ai_host_manager.create_ai_instance(
            ai_type="openclaw",
            name="OpenCLAW模型实例",
            description="部署的OpenCLAW模型实例",
            functions=["text_generation", "code_generation", "knowledge_retrieval"],
            responsibilities=["提供OpenCLAW模型服务", "支持文本生成任务", "支持代码生成任务"],
            config={
                "model_path": "/path/to/openclaw/model",
                "gpu_enabled": True,
                "max_tokens": 2048,
                "temperature": 0.7,
                "top_p": 0.9
            }
        )

        print(f"✅ OpenCLAW模型实例创建成功: {opencwal_instance['instance_id']}")
        print(f"   实例名称: {opencwal_instance['name']}")
        print(f"   实例类型: {opencwal_instance['ai_type']}")

        # 启动AI实例
        print("正在启动OpenCLAW模型实例...")
        if ai_host_manager.start_ai_instance(opencwal_instance['instance_id']):
            print(f"✅ OpenCLAW模型实例已启动")
        else:
            print(f"❌ OpenCLAW模型实例启动失败")
            return False

        # 检查实例健康状态
        print("正在检查实例健康状态...")
        health_status = ai_host_manager.check_ai_instance_health(opencwal_instance['instance_id'])
        if health_status["success"] and health_status["health_status"] == "healthy":
            print(f"✅ OpenCLAW模型实例健康状态: {health_status['health_status']}")
        else:

        # 获取更新后的系统状态
        print("正在获取更新后的系统状态...")
        system_status = ai_host_manager.get_system_status()
        print(f"   系统状态: {system_status['system_status']}")
        print(f"   分布式模式: {system_status['distributed_mode']}")
        print(f"   运行中的AI实例: {system_status['running_ai_instances']}/{system_status['total_ai_instances']}")

        print(f"\n🎉 OpenCLAW模型部署完成!")
        print(f"   实例ID: {opencwal_instance['instance_id']}")
        print(f"   状态: {ai_host_manager.get_ai_instance(opencwal_instance['instance_id'])['status']}")

        return True

    except Exception as e:
        print(f"❌ 部署过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
