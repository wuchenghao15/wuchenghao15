# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
防火墙中间件,用于在请求到达路由之前检查请求是否符合防火墙规则
"""

from flask import request, abort
from app.utils.logging import logger
import logging
import sys


def firewall_middleware(app):
    """防火墙中间件,用于在请求到达路由之前检查请求是否符合防火墙规则"""

    @app.before_request
    def before_request():
        """请求前检查"""

        request_data = {
            "ip": request.remote_addr,
            "port": request.environ.get('SERVER_PORT', 0),
            "method": request.method,
            "url": request.path,
            "headers": dict(request.headers)
        }

        try:
            from app.services.firewall_system import firewall_system
            if not firewall_system.check_request(request_data):
                logger.warning(f"请求被防火墙阻止: {request.method} {request.path} from {request.remote_addr}")
                abort(403, description="请求被防火墙阻止")
        except ImportError:
            pass

        return None

    logger.info("防火墙中间件已注册")
    return app


firewall_middleware_priority = 20