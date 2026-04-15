#!/usr/bin/env python3
"""
防火墙中间件，用于在请求到达路由之前检查请求是否符合防火墙规则
"""

from app.services.firewall_system import firewall_system
from app.utils.logging import logger


def firewall_middleware(app):
    """
    防火墙中间件，用于在请求到达路由之前检查请求是否符合防火墙规则
    
    Args:
        app: Flask应用实例
    """
    @app.before_request
    def before_request():
        """
        请求前检查
        """
        
        # 获取请求信息
        request_data = {
            "ip": request.remote_addr,
            "port": request.environ.get('SERVER_PORT', 0),
            "method": request.method,
            "url": request.path,
            "headers": dict(request.headers)
        }
        
        # 检查请求是否允许通过
        if not firewall_system.check_request(request_data):
            # 请求被阻止
            logger.warning(f"请求被防火墙阻止: {request.method} {request.path} from {request.remote_addr}")
            abort(403, description="请求被防火墙阻止")
        
        # 请求允许通过
        return None


# 中间件优先级
firewall_middleware_priority = 20  # 较高优先级，确保在其他中间件之前执行
