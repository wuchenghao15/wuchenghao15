#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON文件禁用中间件
阻止直接访问JSON文件，强制通过数据库API访问
"""
from flask import request, jsonify
import os

class JSONFileBlockMiddleware:
    def __init__(self, app):
        self.app = app
        self.allowed_json_paths = [
            '/assets/vendor/fontawesome/metadata/',
            '/assets/vendor/crypto-js/',
        ]
    
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        
        if path.endswith('.json'):
            is_allowed = False
            for allowed_path in self.allowed_json_paths:
                if allowed_path in path:
                    is_allowed = True
                    break
            
            if not is_allowed:
                environ['PATH_INFO'] = '/api/data/store/get'
                environ['QUERY_STRING'] = 'file_name=' + os.path.basename(path)
        
        return self.app(environ, start_response)

def init_json_block(app):
    app.wsgi_app = JSONFileBlockMiddleware(app.wsgi_app)
    return app
