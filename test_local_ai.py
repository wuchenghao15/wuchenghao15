#!/usr/bin/env python3
"""
测试本地AI引擎的深度适配功能

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask-app'))

from app.ai.ai_engine_integrator import ai_engine_integrator
from app.services.ai_learning import AILearningSystem
from app.utils.logging import logger


def test_local_ai_engine():
    """测试本地AI引擎"""
    print("=== 测试本地AI引擎 ===")

    # 1. 测试本地引擎实例创建
    print("\n1. 测试本地引擎实例创建")
    local_engine = ai_engine_integrator.create_engine_instance("local")
    if local_engine:
        print("✓ 本地AI引擎实例创建成功")
        print(f"  支持的功能: {', '.join(local_engine.get_supported_features())}")
    else:
        print("✗ 本地AI引擎实例创建失败")

    # 2. 测试本地引擎调用
    print("\n2. 测试本地引擎调用")
    test_prompt = "你好，我是测试用户，请问你能帮我做什么？"
    try:
        response = ai_engine_integrator.call_engine("local", test_prompt, max_tokens=100, temperature=0.7)
        if response and response.get("code") == 0:
            print(f"✓ 本地AI引擎调用成功")
            print(f"  响应: {response['data']['response'][:100]}...")
        else:
    except Exception as e:
        print(f"✗ 本地AI引擎调用异常 - {str(e)}")

    # 3. 测试AI学习系统使用本地引擎
    print("\n3. 测试AI学习系统使用本地引擎")
    try:
        ai_learning = AILearningSystem()
        print(f"  默认AI引擎: {ai_learning._learning_params['ai_engine']}")
        print(f"  备用AI引擎: {ai_learning._learning_params['ai_engine_fallback']}")

        # 测试AI增强学习功能
        print("\n4. 测试AI增强学习功能")
        experience_data = {
            "task": "test_local_ai_adaptation",
            "result": "success",
            "feedback": 1,
            "context": {"engine": "local"},
            "entities": [{"name": "local_ai", "type": "engine"}],
            "relations": [{"subject": "local_ai", "predicate": "supports", "object": "text-generation"}],
            "rules": [{"condition": "engine == 'local'", "action": "use_local_adaptation"}]
        }

        learn_result = ai_learning.learn_from_experience(experience_data)
        if learn_result:
            print("✓ AI学习系统使用本地引擎学习成功")
        else:

    except Exception as e:
        print(f"✗ AI学习系统初始化或学习失败 - {str(e)}")
        import traceback
        traceback.print_exc()
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_local_ai_engine()
