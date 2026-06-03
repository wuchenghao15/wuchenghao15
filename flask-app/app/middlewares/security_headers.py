# -*- coding: utf-8 -*-
import os
# -*- coding: utf-8 -*-
def security_headers_middleware(app):
    """安全头中间件"""

    @app.after_request
    def add_security_headers(response):
        # 添加严格传输安全头(仅生产环境使用HTTPS时启用)
        # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # 添加X-Content-Type-Options头,防止MIME类型嗅探
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # 添加X-Frame-Options头,防止点击劫持
        response.headers['X-Frame-Options'] = 'DENY'

        # 添加X-XSS-Protection头,启用浏览器XSS防护
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # 添加Content-Security-Policy头,防止跨站脚本攻击
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'"

        # 添加Referrer-Policy头,控制Referer头的发送
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # 添加Permissions-Policy头,控制浏览器特性的使用
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), autoplay=()'

        return response

    return app

# 中间件优先级,数字越小优先级越高
# 安全头应该是最高优先级,确保所有响应都有安全头
security_headers_priority = 1
