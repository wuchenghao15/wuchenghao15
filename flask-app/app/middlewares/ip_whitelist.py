# -*- coding: utf-8 -*-
import logging
from flask import request, abort
from app.config import load_config

def ip_whitelist_middleware(app):
    """IP白名单中间件"""
    logger = logging.getLogger('ip_whitelist')

    @app.before_request
    def check_ip_whitelist():
        config = load_config()
        # 只有在测试环境中启用IP白名单
        if config.get('ENV') == 'test':
            # 获取客户端IP
            client_ip = request.remote_addr

            # 获取IP白名单
            ip_whitelist = config.get('SECURITY_CONFIG', {}).get('IP_WHITELIST', [])

            # 如果IP白名单不为空,检查客户端IP是否在白名单中
            if ip_whitelist and client_ip not in ip_whitelist:
                # 记录访问日志
                logger.warning(f"IP {client_ip} 不在白名单中,访问被拒绝")
                # 返回403错误
                abort(403)

    return app
