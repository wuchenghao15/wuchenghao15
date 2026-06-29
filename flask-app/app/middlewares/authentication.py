from flask import request, g
import logging

logger = logging.getLogger('mtscos')


def authentication_middleware(app):
    """认证中间件"""
    @app.before_request
    def before_request():
        pass

    @app.after_request
    def after_request(response):
        return response

    logger.info("[中间件] 认证中间件已注册")
