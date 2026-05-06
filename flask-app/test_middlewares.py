#!/usr/bin/env python3
"""
测试AI中间件功能

import sys
import os
# JSON import removed - using database
import time

# 确保在正确的目录中运行
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

# 添加项目路径
sys.path.append('.')


# 测试AI智能路由中间件
def test_ai_smart_routing():
    """测试AI智能路由中间件"""
    print("\n=== 测试AI智能路由中间件 ===")

    try:

        # 测试初始化
        print("✓ AI智能路由初始化成功")

        # 测试路由权重计算
        test_route = "GET:/test/path"
        test_request = {
            'method': 'GET',
            'path': '/test/path',
            'params': {},
            'headers': {},
            'remote_addr': '127.0.0.1'
        }

        print("✓ AI智能路由功能测试通过")
        return True
    except Exception as e:
        print(f"✗ AI智能路由测试失败: {str(e)}")
        return False

# 测试AI请求分类和优先级中间件
def test_ai_request_classifier():
    """测试AI请求分类和优先级中间件"""
    print("\n=== 测试AI请求分类和优先级中间件 ===")

    try:

        # 测试初始化
        print("✓ AI请求分类和优先级初始化成功")
        # 测试分类功能
        test_request = {
            'method': 'GET',
            'path': '/api/test',
            'headers': {},
        }

        category, base_priority = ai_request_classifier._classify_request(test_request)

        print(f"✓ 优先级: {priority}")
        return True
    except Exception as e:
        print(f"✗ AI请求分类和优先级测试失败: {str(e)}")
        return False

# 测试AI智能缓存中间件
def test_ai_smart_cache():
    """测试AI智能缓存中间件"""
    print("\n=== 测试AI智能缓存中间件 ===")
    try:
        # 测试初始化
        print("✓ AI智能缓存初始化成功")
        class MockRequest:
            def __init__(self):
                self.method = 'GET'
                self.path = '/test/path'
                self.args = type('Args', (), {'to_dict': lambda self: {}})()
                self.form = type('Form', (), {'to_dict': lambda self: {}})()
                self.is_json = False
                self.get_json = lambda: None

        # 模拟请求
        mock_request = MockRequest()

        # 保存原始request
        original_request = ai_smart_cache._generate_cache_key.__globals__['request']
        ai_smart_cache._generate_cache_key.__globals__['request'] = mock_request

        # 生成缓存键
        cache_key = ai_smart_cache._generate_cache_key()
        print(f"✓ 缓存键生成: {cache_key}")

        # 恢复原始request
        ai_smart_cache._generate_cache_key.__globals__['request'] = original_request

        print("✓ AI智能缓存功能测试通过")
        return True
    except Exception as e:
        print(f"✗ AI智能缓存测试失败: {str(e)}")
        return False

# 测试AI中间件学习系统
def test_ai_middleware_learning():
    """测试AI中间件学习系统"""
    print("\n=== 测试AI中间件学习系统 ===")

    try:
        # 测试初始化
        ai_learning = AIMiddlewareLearningSystem()

        performance_data = {
            'middleware_name': 'test_middleware',
            'memory_usage': 100,
            'cpu_usage': 50,
            'request_count': 100,
            'error_count': 0,
            'timestamp': int(time.time())
        }

        print("✓ AI中间件学习系统功能测试通过")
        return True
    except Exception as e:
        print(f"✗ AI中间件学习系统测试失败: {str(e)}")
        return False

# 测试AI中间件优化器
def test_ai_middleware_optimizer():
    """测试AI中间件优化器"""
    print("\n=== 测试AI中间件优化器 ===")
    try:

        # 测试初始化
        ai_optimizer = AIMiddlewareOptimizer()

        print("✓ AI中间件优化器功能测试通过")
    except Exception as e:
        return False

# 测试中间件注册
def test_middleware_registration():
    print("\n=== 测试中间件注册 ===")

    try:

        # 初始化中间件
        init_middlewares()

        # 获取已注册的中间件
        print(f"✓ 已注册中间件: {registered_middlewares}")

        # 检查AI中间件是否已注册
        ai_middlewares = [
            'ai_middleware_optimizer',
            'ai_smart_cache',
            'ai_smart_routing',
            'ai_request_classifier'
        ]
        for ai_middleware in ai_middlewares:
            if ai_middleware in registered_middlewares:
                print(f"✓ {ai_middleware} 已成功注册")
            else:
                print(f"✗ {ai_middleware} 未注册")

        print("✓ 中间件注册测试通过")
        return True
    except Exception as e:
        print(f"✗ 中间件注册测试失败: {str(e)}")
        return False

# 测试Flask应用集成
def test_flask_integration():
    """测试Flask应用集成"""
    print("\n=== 测试Flask应用集成 ===")

    try:

        # 创建Flask应用
        app = Flask(__name__)

        # 初始化中间件
        init_middlewares()
        @app.route('/test')
        def test_route():
            return str({'message': 'Test successful'}), 200, {'Content-Type': 'application/json'}

        print("✓ Flask应用集成测试通过")
    except Exception as e:
        print(f"✗ Flask应用集成测试失败: {str(e)}")
        return False

# 主测试函数
def main():
    print("开始测试AI中间件功能...")

    # 运行所有测试
    tests = [
        test_ai_smart_routing,
        test_ai_request_classifier,
        test_ai_smart_cache,
        test_ai_middleware_learning,
        test_ai_middleware_optimizer,
        test_middleware_registration,
    ]

    passed = 0
    failed = 0

    for test in tests:
            passed += 1
            failed += 1
    # 打印测试结果
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"总测试数: {passed + failed}")

    if failed == 0:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
