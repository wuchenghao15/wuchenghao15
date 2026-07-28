#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS API文档服务 提供Swagger/OpenAPI文档自动生成功能 """

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class APIDocEndpoint:
    """API端点文档"""
    
    def __init__(self, path: str, method: str, summary: str = '',
                 description: str = '', parameters: List[Dict[str, Any]] = None,
                 request_body: Dict[str, Any] = None,
                 responses: Dict[str, Dict[str, Any]] = None,
                 tags: List[str] = None, security: List[Dict[str, List[str]]] = None):
        self.path = path
        self.method = method
        self.summary = summary
        self.description = description
        self.parameters = parameters or []
        self.request_body = request_body
        self.responses = responses or {}
        self.tags = tags or []
        self.security = security or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'path': self.path,
            'method': self.method,
            'summary': self.summary,
            'description': self.description,
            'parameters': self.parameters,
            'request_body': self.request_body,
            'responses': self.responses,
            'tags': self.tags,
            'security': self.security
        }

class APIDocService:
    """API文档服务"""
    
    def __init__(self):
        self.endpoints: Dict[str, APIDocEndpoint] = {}
        self.tags: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._init_openapi_spec()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'api_doc_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'openapi_version': '3.0.3',
            'title': 'MTSCOS AI API',
            'description': 'MTSCOS AI系统API文档',
            'version': 'v9.6.0',
            'contact': {
                'name': 'MTSCOS Support',
                'email': 'support@mtscos.com'
            },
            'servers': [
                {'url': 'http://localhost:5000', 'description': '本地开发环境'},
                {'url': 'http://api.mtscos.com', 'description': '生产环境'}
            ]
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'api_doc_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS api_doc_endpoints ( id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, method TEXT NOT NULL, summary TEXT, description TEXT, parameters TEXT, request_body TEXT, responses TEXT, tags TEXT, security TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS api_doc_tags ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE UNIQUE INDEX IF NOT EXISTS idx_api_doc_path_method ON api_doc_endpoints(path, method) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[API文档] 初始化数据库失败: {e}")
    
    def _init_openapi_spec(self):
        """初始化OpenAPI规范"""
        self.openapi_spec = {
            'openapi': self.config['openapi_version'],
            'info': {
                'title': self.config['title'],
                'description': self.config['description'],
                'version': self.config['version'],
                'contact': self.config['contact']
            },
            'servers': self.config['servers'],
            'paths': {},
            'components': {
                'schemas': {},
                'securitySchemes': {
                    'bearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT'
                    },
                    'apiKeyAuth': {
                        'type': 'apiKey',
                        'in': 'header',
                        'name': 'X-API-Key'
                    }
                }
            },
            'tags': []
        }
    
    def register_endpoint(self, path: str, method: str, summary: str = '',
                         description: str = '', parameters: List[Dict[str, Any]] = None,
                         request_body: Dict[str, Any] = None,
                         responses: Dict[str, Dict[str, Any]] = None,
                         tags: List[str] = None, security: List[Dict[str, List[str]]] = None):
        """注册API端点文档"""
        key = f"{method.upper()}_{path}"
        
        endpoint = APIDocEndpoint(
            path=path,
            method=method.upper(),
            summary=summary,
            description=description,
            parameters=parameters or [],
            request_body=request_body,
            responses=responses or {},
            tags=tags or [],
            security=security or []
        )
        
        with self.lock:
            self.endpoints[key] = endpoint
        
        self._save_endpoint_to_db(endpoint)
        
        for tag in tags or []:
            self.add_tag(tag)
        
        self._update_openapi_spec()
        
        logger(f"[API文档] 注册端点: {method.upper()} {path}")
    
    def _save_endpoint_to_db(self, endpoint: APIDocEndpoint):
        """保存端点到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO api_doc_endpoints (path, method, summary, description, parameters, request_body, responses, tags, security, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                endpoint.path, endpoint.method, endpoint.summary,
                endpoint.description,
                json.dumps(endpoint.parameters),
                json.dumps(endpoint.request_body) if endpoint.request_body else None,
                json.dumps(endpoint.responses),
                json.dumps(endpoint.tags),
                json.dumps(endpoint.security),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[API文档] 保存端点失败: {e}")
    
    def add_tag(self, name: str, description: str = ''):
        """添加标签"""
        if name in self.tags:
            return
        
        self.tags[name] = {'name': name, 'description': description}
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('INSERT OR IGNORE INTO api_doc_tags (name, description) VALUES (?, ?)',
                          (name, description))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[API文档] 添加标签失败: {e}")
    
    def _update_openapi_spec(self):
        """更新OpenAPI规范"""
        paths = {}
        
        for key, endpoint in self.endpoints.items():
            method = endpoint.method.lower()
            path = endpoint.path
            
            if path not in paths:
                paths[path] = {}
            
            paths[path][method] = {
                'summary': endpoint.summary,
                'description': endpoint.description,
                'tags': endpoint.tags
            }
            
            if endpoint.parameters:
                paths[path][method]['parameters'] = endpoint.parameters
            
            if endpoint.request_body:
                paths[path][method]['requestBody'] = endpoint.request_body
            
            if endpoint.responses:
                paths[path][method]['responses'] = endpoint.responses
            
            if endpoint.security:
                paths[path][method]['security'] = endpoint.security
        
        self.openapi_spec['paths'] = paths
        self.openapi_spec['tags'] = list(self.tags.values())
    
    def get_openapi_spec(self) -> Dict[str, Any]:
        """获取OpenAPI规范"""
        return self.openapi_spec
    
    def generate_swagger_json(self) -> str:
        """生成Swagger JSON"""
        return json.dumps(self.openapi_spec, indent=2, ensure_ascii=False)
    
    def generate_swagger_yaml(self) -> str:
        """生成Swagger YAML"""
        try:
            import yaml
            return yaml.dump(self.openapi_spec, default_flow_style=False, allow_unicode=True)
        except ImportError:
            return self.generate_swagger_json()
    
    def generate_html_docs(self) -> str:
        """生成HTML文档"""
        swagger_json = self.generate_swagger_json()
        
        html = f"""<!DOCTYPE html> <html lang="zh-CN"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>MTSCOS AI API文档</title> <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.min.css"> <style> body {{ margin: 0; }} #swagger-ui {{ height: 100vh; }} </style> </head> <body> <div id="swagger-ui"></div> <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui-bundle.min.js"></script> <script> const ui = SwaggerUIBundle({{ spec: {swagger_json}, dom_id: '#swagger-ui', deepLinking: true, presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset], layout: 'StandaloneLayout' }}); </script> </body> </html>"""
        
        return html
    
    def save_docs(self, output_dir: str = 'docs/api'):
        """保存文档"""
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, 'swagger.json'), 'w', encoding='utf-8') as f:
            f.write(self.generate_swagger_json())
        
        with open(os.path.join(output_dir, 'swagger.yaml'), 'w', encoding='utf-8') as f:
            f.write(self.generate_swagger_yaml())
        
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(self.generate_html_docs())
        
        logger(f"[API文档] 文档已保存到 {output_dir}")
    
    def get_endpoint(self, path: str, method: str) -> Optional[APIDocEndpoint]:
        """获取端点文档"""
        key = f"{method.upper()}_{path}"
        return self.endpoints.get(key)
    
    def get_endpoints(self, tag: str = None) -> List[APIDocEndpoint]:
        """获取端点列表"""
        results = []
        
        with self.lock:
            for endpoint in self.endpoints.values():
                if tag and tag not in endpoint.tags:
                    continue
                results.append(endpoint)
        
        return results
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """获取所有标签"""
        return list(self.tags.values())
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'openapi_version': self.config['openapi_version'],
            'api_version': self.config['version'],
            'title': self.config['title'],
            'total_endpoints': len(self.endpoints),
            'total_tags': len(self.tags)
        }
    
    def start(self):
        """启动API文档服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self._load_endpoints_from_db()
        logger(f"[API文档] API文档服务已启动")
    
    def _load_endpoints_from_db(self):
        """从数据库加载端点"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT path, method, summary, description, parameters, request_body, responses, tags, security FROM api_doc_endpoints')
            
            for row in cursor.fetchall():
                path, method, summary, description, parameters, request_body, responses, tags, security = row
                
                self.register_endpoint(
                    path=path,
                    method=method,
                    summary=summary,
                    description=description,
                    parameters=json.loads(parameters) if parameters else [],
                    request_body=json.loads(request_body) if request_body else None,
                    responses=json.loads(responses) if responses else {},
                    tags=json.loads(tags) if tags else [],
                    security=json.loads(security) if security else []
                )
            
            conn.close()
            logger(f"[API文档] 从数据库加载了 {len(self.endpoints)} 个端点")
        except Exception as e:
            logger(f"[API文档] 加载端点失败: {e}")
    
    def stop(self):
        """停止API文档服务"""
        self.is_running = False
        logger(f"[API文档] API文档服务已停止")

api_doc_service = APIDocService()

def api_doc(path: str, method: str = 'GET', summary: str = '', description: str = '',
           parameters: List[Dict[str, Any]] = None, request_body: Dict[str, Any] = None,
           responses: Dict[str, Dict[str, Any]] = None, tags: List[str] = None,
           security: List[Dict[str, List[str]]] = None):
    """装饰器：注册API文档"""
    def decorator(func):
        api_doc_service.register_endpoint(
            path=path,
            method=method,
            summary=summary,
            description=description,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            tags=tags,
            security=security
        )
        return func
    return decorator
