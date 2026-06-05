# -*- coding: utf-8 -*-
# AI请求分类器中间件

import logging

logger = logging.getLogger(__name__)

def ai_request_classifier_middleware(app):
    """AI请求分类器中间件"""
    logger.info("[AI分类] 请求分类器中间件已加载")
    
    @app.before_request
    def classify_before():
        pass
    
    @app.after_request
    def classify_after(response):
        return response
    
    return app