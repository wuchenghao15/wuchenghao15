#!/usr/bin/env python3
"""
修复后的拦截启动脚本，使用正确实现的模块拦截器
import sys
import os
import types

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[修复拦截启动] 正在初始化...")

# 1. 创建一个正确实现接口的拦截器类
class LearningModuleSpec(importlib.machinery.ModuleSpec):
    """自定义的模块规格类"""
    pass

class LearningModuleLoader(importlib.abc.Loader):
    """学习模块加载器"""
    def create_module(self, spec):
        # 创建一个假的learning模块
        fake_learning = types.ModuleType('app.ai.learning')

        # 添加必要的类和方法，避免ImportError
        class FakeLearningAI:
            def __init__(self, config=None):
                # 忽略config参数，避免KeyError
                print("[修复拦截启动] 创建了FakeLearningAI实例")
                self.model_path = 'models/'

            def learn(self, data):
                print(f"[修复拦截启动] FakeLearningAI.learn() 被调用，数据: {data}")
                return {}

        # 添加AILearning类，用于处理另一个导入
        class FakeAILearning:
            def __init__(self, config=None):
                self.model_path = 'models/'

                print(f"[修复拦截启动] FakeAILearning.process() 被调用，数据: {data}")
                return {}

        # 将类添加到模块中
        fake_learning.AILearning = FakeAILearning

        print("[修复拦截启动] 已创建假的app.ai.learning模块")
        return fake_learning

    def exec_module(self, module):
        # 不需要执行任何代码
        pass
class LearningModuleFinder(importlib.abc.MetaPathFinder):
    """学习模块查找器"""
    def find_spec(self, fullname, path, target=None):
        if fullname == 'app.ai.learning':
            print(f"[修复拦截启动] 拦截到模块导入: {fullname}")
            # 创建一个模块规格
            spec = LearningModuleSpec(fullname, LearningModuleLoader())
            return spec
        return None

# 2. 将拦截器添加到sys.meta_path
print("[修复拦截启动] 添加模块导入拦截器...")
sys.meta_path.insert(0, LearningModuleFinder())

# 3. 尝试启动服务器
print("[修复拦截启动] 正在启动服务器...")
try:
    # 直接执行start_server.py的内容
    exec(open('start_server.py').read())
    print("[修复拦截启动] 服务器启动成功！")
except Exception as e:
    print(f"[修复拦截启动] 服务器启动失败: {e}")
    import traceback
    traceback.print_exc()
