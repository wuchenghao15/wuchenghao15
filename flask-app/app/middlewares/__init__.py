# -*- coding: utf-8 -*-
# Middlewares package
import logging
logger = logging.getLogger(__name__)
import os
import importlib
from typing import Dict, List, Callable, Optional


from app.middlewares.ai_brain_middleware import AIBrainMiddleware

class MiddlewareManager:
    """
    中间件管理器,用于统一管理和注册中间件

    def __init__(self):
        # 中间件注册表,格式:{middleware_name: {func: middleware_func, priority: int}}
        self.middlewares = {}
        # 中间件优先级列表,用于按优先级排序
        self.priority_list = []

    def register_middleware(self, name: str, middleware_func: Callable, priority: int = 50):
        注册中间件

        Args:
            name: 中间件名称
            middleware_func: 中间件函数
            priority: 优先级,数字越小优先级越高
        if name not in self.middlewares:
            self.middlewares[name] = {
                'func': middleware_func,
                'priority': priority
            }
            self.priority_list.append(name)
            # 按优先级排序
            self.priority_list.sort(key=lambda x: self.middlewares[x]['priority'])
            print(f"✓ 注册中间件: {name} (优先级: {priority})")

    def get_middleware(self, name: str) -> Optional[Dict]:
        获取中间件

        Args:
            name: 中间件名称

        Returns:
    pass
        return self.middlewares.get(name)
    def unregister_middleware(self, name: str):
        注销中间件

        Args:
            name: 中间件名称
        if name in self.middlewares:
            del self.middlewares[name]
            if name in self.priority_list:
                self.priority_list.remove(name)

    def apply_middlewares(self, app):
    pass

        Args:
            app: Flask应用实例
        print("开始应用中间件...")
        for middleware_name in self.priority_list:
            middleware = self.middlewares[middleware_name]
            try:
                middleware['func'](app)
                print(f"✓ 应用中间件: {middleware_name} (优先级: {middleware['priority']})")
                print(f"✗ 应用中间件 {middleware_name} 失败: {str(e)}")
        print("中间件应用完成")

    def auto_discover_middlewares(self, module_path: str = 'app.middlewares'):
        自动发现中间件

        Args:
            module_path: 中间件模块路径
        print("开始自动发现中间件...")

        # 获取中间件目录路径
        middlewares_dir = os.path.dirname(os.path.abspath(__file__))

        # 遍历中间件目录下的所有Python文件
        for file_name in os.listdir(middlewares_dir):
            if file_name.endswith('.py') and file_name != '__init__.py':
                full_module_name = f"{module_path}.{module_name}"

                try:
                    # 导入模块
                    module = importlib.import_module(full_module_name)

                    # 遍历模块中的所有属性,查找中间件函数
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        # 中间件函数命名约定:*_middleware
                        if callable(attr) and attr_name.endswith('_middleware'):
                            # 提取中间件名称
                            middleware_name = attr_name[:-11]  # 去掉_middleware后缀
                            # 默认优先级
                            priority = 50

                            # 检查是否有优先级配置
                            if hasattr(module, f"{middleware_name}_priority"):
                                priority = getattr(module, f"{middleware_name}_priority")
                            # 注册中间件
                            self.register_middleware(middleware_name, attr, priority)
                except Exception as e:
                    print(f"✗ 自动发现中间件 {module_name} 失败: {str(e)}")

        print("中间件自动发现完成")


# 创建全局中间件管理器实例
middleware_manager = MiddlewareManager()


# 预注册已知的中间件
def init_middlewares():
    初始化中间件,包括自动发现和手动注册
    # 1. 自动发现中间件
    middleware_manager.auto_discover_middlewares()

    # 2. 手动注册特定中间件(如果需要)
    # 注册AI脑库中间件
        "ai_brain_request_logger",
        AIBrainMiddleware.request_logger,
        priority=45
    )
    middleware_manager.register_middleware(
        "ai_brain_response_logger",
        AIBrainMiddleware.response_logger,
        priority=40
    )
    middleware_manager.register_middleware(
        "ai_brain_rate_limiter",
        AIBrainMiddleware.api_rate_limiter,
        priority=35
    )
    middleware_manager.register_middleware(
        "ai_brain_cors",
        AIBrainMiddleware.cors_middleware,
        priority=30
    )

    # 3. 注册AI中间件学习系统中间件
    from app.middlewares.ai_middleware_learning import ai_middleware_learning_middleware
    middleware_manager.register_middleware(
        "ai_middleware_learning",
        ai_middleware_learning_middleware,
        priority=10
    )

    # 4. 注册AI中间件优化器中间件
    from app.middlewares.ai_middleware_optimizer import ai_middleware_optimizer_middleware
    middleware_manager.register_middleware(
        "ai_middleware_optimizer",
        ai_middleware_optimizer_middleware,
        priority=5
    )

    # 5. 注册AI智能缓存中间件
    from app.middlewares.ai_smart_cache import ai_smart_cache_middleware
    middleware_manager.register_middleware(
        "ai_smart_cache",
        ai_smart_cache_middleware,
        priority=15
    )

    # 6. 注册AI智能路由中间件
    from app.middlewares.ai_smart_routing import ai_smart_routing_middleware
    middleware_manager.register_middleware(
        "ai_smart_routing",
        ai_smart_routing_middleware,
        priority=20
    )

    # 7. 注册AI请求分类和优先级中间件
    from app.middlewares.ai_request_classifier import ai_request_classifier_middleware
    middleware_manager.register_middleware(
        "ai_request_classifier",
        ai_request_classifier_middleware,
        priority=25
    )

    # 8. 注册AI自学习中间件
    from app.middlewares.ai_self_learning_middleware import ai_self_learning_middleware
    middleware_manager.register_middleware(
        "ai_self_learning",
        ai_self_learning_middleware,
        priority=5
    )
    # 例如:middleware_manager.register_middleware('custom', custom_middleware, priority=10)


# 导出中间件管理器
__all__ = ['middleware_manager', 'init_middlewares']


def do_work(**kwargs):
    """