#!/usr/bin/env python3
"""
测试所有AI引擎的深度适配是否成功

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask-app'))

from app.ai.ai_engine_integrator import ai_engine_integrator
from app.utils.logging import logger


def test_ai_engine_integrator():
    """测试AI引擎集成器"""
    print("=== 测试AI引擎集成器 ===")

    # 1. 测试引擎列表
    supported_engines = ai_engine_integrator.get_supported_engines()
    print(f"支持的引擎数量: {len(supported_engines)}")
    print(f"支持的引擎: {', '.join(supported_engines)}")

    # 2. 测试引擎配置
    print("\n=== 测试引擎配置 ===")
    for engine_type in supported_engines:
        config = ai_engine_integrator.get_engine_config(engine_type)
        if config:
            print(f"\n{engine_type} 配置:")
            print(f"  API密钥: {'已配置' if config.get('api_key') else '未配置'}")
            print(f"  模型: {config.get('model')}")
            print(f"  最大tokens: {config.get('max_tokens')}")
            print(f"  温度: {config.get('temperature')}")
            print(f"  超时: {config.get('timeout')}秒")
            print(f"  重试次数: {config.get('retry_count')}")
            print(f"  支持的功能: {', '.join(config.get('supported_features', []))}")

    # 3. 测试引擎实例创建
    print("\n=== 测试引擎实例创建 ===")
    for engine_type in supported_engines:
            engine = ai_engine_integrator.create_engine_instance(engine_type)
            if engine:
                print(f"✓ {engine_type}: 实例创建成功")
                # 测试功能支持检查
                features = engine.get_supported_features()
                if features:
                    print(f"  支持的功能: {', '.join(features[:3])}{'...' if len(features) > 3 else ''}")
        except Exception as e:
            print(f"✗ {engine_type}: 实例创建失败 - {str(e)}")

    # 4. 测试健康检查
    print("\n=== 测试引擎健康检查 ===")
    healthy_engines = ai_engine_integrator.get_healthy_engines()
    print(f"健康的引擎数量: {len(healthy_engines)}")
    print(f"健康的引擎: {', '.join(healthy_engines) if healthy_engines else '无'}")

    # 5. 测试最佳引擎选择
    print("\n=== 测试最佳引擎选择 ===")
    preferred_engine = "gemini"
    best_engine = ai_engine_integrator.get_best_engine(preferred_engine)
    print(f"首选引擎: {preferred_engine}")
    print(f"最佳引擎: {best_engine}")

    # 6. 测试引擎调用（使用简单的健康检查）
    print("\n=== 测试引擎调用 ===")
    test_prompt = "健康检查"
    for engine_type in ["gemini", "minimax", "local"]:
        try:
            response = ai_engine_integrator.call_engine(engine_type, test_prompt, max_tokens=20, temperature=0.1)
                print(f"✓ {engine_type}: 调用成功")
                print(f"  响应: {response['data']['response'][:50]}...")
            else:
                print(f"✗ {engine_type}: 调用失败 - {response.get('message') if response else '无响应'}")
        except Exception as e:
            print(f"✗ {engine_type}: 调用异常 - {str(e)}")



if __name__ == "__main__":
    test_ai_engine_integrator()
