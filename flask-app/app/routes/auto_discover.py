# -*- coding: utf-8 -*-
"""
自动路由发现管理器
自动扫描app/api/和app/routes/目录，注册所有蓝图
"""

import os
import logging
import importlib
from flask import Flask

logger = logging.getLogger(__name__)


class AutoRouteDiscoverer:
    """自动路由发现器"""

    def __init__(self, app: Flask = None):
        self.app = app
        self.registered_blueprints = []

    def register_with_app(self, app: Flask):
        """注册到Flask应用"""
        self.app = app

    def discover_and_register(self):
        """自动发现并注册所有蓝图"""
        if not self.app:
            logger.error("自动路由发现: 应用实例未设置")
            return

        registered_count = 0
        failed_count = 0

        # 扫描 app/api/ 目录
        api_dir = os.path.join(os.path.dirname(__file__), 'api')
        registered, failed = self._scan_directory(api_dir, 'app.api.')
        registered_count += registered
        failed_count += failed

        # 扫描 app/routes/ 目录
        routes_dir = os.path.join(os.path.dirname(__file__), 'routes')
        registered, failed = self._scan_directory(routes_dir, 'app.routes.')
        registered_count += registered
        failed_count += failed

        # 扫描 app/blueprints/ 目录
        blueprints_dir = os.path.join(os.path.dirname(__file__), 'blueprints')
        registered, failed = self._scan_directory(blueprints_dir, 'app.blueprints.')
        registered_count += registered
        failed_count += failed

        # 扫描 app/views/ 目录
        views_dir = os.path.join(os.path.dirname(__file__), 'views')
        registered, failed = self._scan_directory(views_dir, 'app.views.')
        registered_count += registered
        failed_count += failed

        logger.info(f"自动路由发现完成: 成功注册 {registered_count} 个蓝图, 失败 {failed_count} 个")
        return registered_count, failed_count

    def _scan_directory(self, directory: str, module_prefix: str):
        """扫描指定目录"""
        if not os.path.exists(directory):
            return 0, 0

        registered = 0
        failed = 0

        for filename in sorted(os.listdir(directory)):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue

            module_name = filename[:-3]
            module_path = f"{module_prefix}{module_name}"

            try:
                module = importlib.import_module(module_path)

                # 查找所有Blueprint实例
                blueprints = []
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and 'Blueprint' in str(type(attr).__mro__):
                        continue
                    try:
                        if hasattr(attr, 'register_blueprint'):
                            blueprints.append((attr_name, attr))
                    except Exception:
                        pass

                # 注册所有找到的蓝图
                for name, blueprint in blueprints:
                    self.app.register_blueprint(blueprint)
                    self.registered_blueprints.append({
                        'name': name,
                        'module': module_path,
                        'url_prefix': getattr(blueprint, 'url_prefix', None)
                    })
                    registered += 1
                    logger.debug(f"自动注册蓝图: {name} ({module_path})")

            except ImportError as e:
                logger.debug(f"跳过模块 {module_path}: 导入错误 - {str(e)[:50]}")
                failed += 1
            except Exception as e:
                logger.warning(f"注册模块 {module_path} 失败: {str(e)[:50]}")
                failed += 1

        return registered, failed

    def get_registered_blueprints(self):
        """获取已注册的蓝图列表"""
        return self.registered_blueprints

    def list_all_routes(self):
        """列出所有注册的路由"""
        if not self.app:
            return []

        routes = []
        for rule in self.app.url_map.iter_rules():
            routes.append({
                'rule': str(rule),
                'endpoint': rule.endpoint,
                'methods': sorted([m for m in rule.methods if m not in ['OPTIONS', 'HEAD']])
            })
        return routes


# 创建全局路由发现器实例
route_discoverer = AutoRouteDiscoverer()


def init_auto_routes(app: Flask):
    """初始化自动路由发现"""
    route_discoverer.register_with_app(app)
    registered, failed = route_discoverer.discover_and_register()
    return {
        'registered': registered,
        'failed': failed,
        'total_routes': len(route_discoverer.list_all_routes())
    }
