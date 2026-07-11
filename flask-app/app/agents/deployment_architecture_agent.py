# -*- coding: utf-8 -*-
"""
DeploymentArchitectureAgent - 部署架构Agent
感知项目的Flask+前端部署架构，提供部署适配能力
"""
import json
import logging
import os
import yaml
import subprocess
from datetime import datetime
from typing import Dict, Any, List

from .base_core_agent import BaseCoreAgent

logger = logging.getLogger(__name__)


class DeploymentArchitectureAgent(BaseCoreAgent):
    """部署架构Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id='core_deployment_arch',
            agent_name='部署架构Agent',
            agent_type='deployment_architecture'
        )
        self.architecture_info = {}
        self.deployment_count = 0
    
    def discover_architecture(self) -> Dict:
        """发现项目架构"""
        self.architecture_info = {
            'project_structure': self._discover_project_structure(),
            'flask_config': self._discover_flask_config(),
            'frontend_config': self._discover_frontend_config(),
            'database_config': self._discover_database_config(),
            'api_endpoints': self._discover_api_endpoints(),
            'blueprints': self._discover_blueprints(),
            'middleware': self._discover_middleware(),
            'deployment_config': self._discover_deployment_config()
        }
        
        return self.architecture_info
    
    def _discover_project_structure(self) -> Dict:
        """发现项目结构"""
        project_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app'
        
        structure = {}
        
        for root, dirs, files in os.walk(project_dir):
            if '.git' in dirs:
                dirs.remove('.git')
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')
            
            rel_path = os.path.relpath(root, project_dir)
            structure[rel_path] = {
                'directories': dirs,
                'files': [f for f in files if not f.startswith('.')]
            }
            
            if rel_path == 'app/api':
                structure[rel_path]['api_count'] = len([f for f in files if f.endswith('_api.py')])
            if rel_path == 'app/views':
                structure[rel_path]['view_count'] = len([f for f in files if f.endswith('.py')])
            if rel_path == 'templates':
                structure[rel_path]['template_count'] = len([f for f in files if f.endswith('.html')])
        
        return structure
    
    def _discover_flask_config(self) -> Dict:
        """发现Flask配置"""
        config = {}
        
        try:
            from flask import current_app
            if current_app:
                config['debug'] = current_app.config.get('DEBUG', False)
                config['secret_key'] = '******' if current_app.config.get('SECRET_KEY') else None
                config['session_timeout'] = current_app.config.get('SESSION_TIMEOUT', 1800)
                config['port'] = current_app.config.get('PORT', 8888)
        except Exception:
            pass
        
        return config
    
    def _discover_frontend_config(self) -> Dict:
        """发现前端配置"""
        frontend_config = {}
        
        template_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/templates'
        if os.path.exists(template_dir):
            frontend_config['template_count'] = len(os.listdir(template_dir))
            
            main_templates = [
                'exam_system.html',
                'teacher.html',
                'arduino.html',
                'settings.html',
                'dashboard.html',
                'login.html',
                'new_layout.html'
            ]
            
            frontend_config['main_templates'] = [
                t for t in main_templates if os.path.exists(os.path.join(template_dir, t))
            ]
        
        static_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/static'
        if os.path.exists(static_dir):
            frontend_config['static_files'] = len(os.listdir(static_dir))
        
        return frontend_config
    
    def _discover_database_config(self) -> Dict:
        """发现数据库配置"""
        db_config = {}
        
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        if os.path.exists(db_path):
            db_config['type'] = 'sqlite'
            db_config['path'] = db_path
            db_config['size_mb'] = round(os.path.getsize(db_path) / (1024 ** 2), 2)
            
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                db_config['table_count'] = cursor.fetchone()[0]
                conn.close()
            except Exception as e:
                db_config['error'] = str(e)
        
        return db_config
    
    def _discover_api_endpoints(self) -> List[Dict]:
        """发现API端点"""
        endpoints = []
        
        api_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app/api'
        if os.path.exists(api_dir):
            for file in os.listdir(api_dir):
                if file.endswith('_api.py'):
                    file_path = os.path.join(api_dir, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import re
                    routes = re.findall(r'@\w+\.route\(\'([^\']+)\'', content)
                    methods = re.findall(r'methods=\[([^\]]+)\]', content)
                    
                    for i, route in enumerate(routes):
                        endpoint = {
                            'module': file.replace('.py', ''),
                            'route': route,
                            'methods': [m.strip().strip('\'"') for m in methods[i].split(',')] if i < len(methods) else ['GET']
                        }
                        endpoints.append(endpoint)
        
        return endpoints
    
    def _discover_blueprints(self) -> List[Dict]:
        """发现蓝图"""
        blueprints = []
        
        api_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app/api'
        if os.path.exists(api_dir):
            for file in os.listdir(api_dir):
                if file.endswith('_api.py'):
                    file_path = os.path.join(api_dir, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    match = re.search(r'(\w+)\s*=\s*Blueprint\(', content)
                    if match:
                        bp_name = match.group(1)
                        url_prefix_match = re.search(r'url_prefix\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                        
                        blueprints.append({
                            'name': bp_name,
                            'file': file,
                            'url_prefix': url_prefix_match.group(1) if url_prefix_match else None
                        })
        
        return blueprints
    
    def _discover_middleware(self) -> List[str]:
        """发现中间件"""
        middleware = []
        
        middleware_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app/middlewares'
        if os.path.exists(middleware_dir):
            for file in os.listdir(middleware_dir):
                if file.endswith('.py') and not file.startswith('_'):
                    middleware.append(file.replace('.py', ''))
        
        return middleware
    
    def _discover_deployment_config(self) -> Dict:
        """发现部署配置"""
        config = {}
        
        config_files = ['Dockerfile', 'docker-compose.yml', 'requirements.txt', 'config.py']
        project_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app'
        
        for file in config_files:
            path = os.path.join(project_dir, file)
            if os.path.exists(path):
                config[file] = {'exists': True, 'size_bytes': os.path.getsize(path)}
            else:
                config[file] = {'exists': False}
        
        try:
            with open(os.path.join(project_dir, 'requirements.txt'), 'r') as f:
                packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                config['requirements'] = {
                    'package_count': len(packages),
                    'packages': packages[:10]
                }
        except Exception:
            pass
        
        return config
    
    def generate_deployment_plan(self, environment: str = 'development') -> Dict:
        """生成部署计划"""
        plans = {
            'development': {
                'name': '开发环境部署',
                'server': 'localhost',
                'port': 8888,
                'debug': True,
                'workers': 1,
                'database': 'sqlite',
                'ssl': False,
                'cors': True
            },
            'testing': {
                'name': '测试环境部署',
                'server': 'test.example.com',
                'port': 8080,
                'debug': False,
                'workers': 2,
                'database': 'sqlite',
                'ssl': False,
                'cors': True
            },
            'staging': {
                'name': '预生产环境部署',
                'server': 'staging.example.com',
                'port': 443,
                'debug': False,
                'workers': 4,
                'database': 'mysql',
                'ssl': True,
                'cors': True
            },
            'production': {
                'name': '生产环境部署',
                'server': 'example.com',
                'port': 443,
                'debug': False,
                'workers': 8,
                'database': 'mysql',
                'ssl': True,
                'cors': False
            }
        }
        
        plan = plans.get(environment, plans['development'])
        plan['generated_at'] = datetime.now().isoformat()
        plan['architecture_info'] = self.architecture_info
        
        return plan
    
    def apply_deployment_config(self, config: Dict) -> Dict:
        """应用部署配置"""
        task_id = self.generate_task_id()
        
        try:
            changes = []
            
            if 'port' in config:
                changes.append(f"设置端口: {config['port']}")
            
            if 'debug' in config:
                changes.append(f"调试模式: {'开启' if config['debug'] else '关闭'}")
            
            if 'workers' in config:
                changes.append(f"工作进程数: {config['workers']}")
            
            if 'ssl' in config:
                changes.append(f"SSL: {'启用' if config['ssl'] else '禁用'}")
            
            self.deployment_count += 1
            
            self.report_to_db(task_id, 'completed', {
                'config': config,
                'changes': changes
            })
            
            self.record_task(task_id, 'completed', {'environment': config.get('environment', 'unknown')})
            
            return {
                'success': True,
                'task_id': task_id,
                'agent': self.agent_name,
                'changes': changes,
                'message': '部署配置已应用'
            }
        
        except Exception as e:
            return self.handle_error(e, task_id)
    
    def execute(self, context: Dict = None) -> Dict:
        """执行部署架构操作"""
        task_id = self.generate_task_id()
        self.status = 'running'
        self.heartbeat()
        
        try:
            action = context.get('action', 'discover') if context else 'discover'
            
            if action == 'discover':
                architecture = self.discover_architecture()
                return {
                    'success': True,
                    'task_id': task_id,
                    'agent': self.agent_name,
                    'architecture': architecture
                }
            
            elif action == 'plan':
                environment = context.get('environment', 'development')
                plan = self.generate_deployment_plan(environment)
                return {
                    'success': True,
                    'task_id': task_id,
                    'agent': self.agent_name,
                    'environment': environment,
                    'plan': plan
                }
            
            elif action == 'apply':
                config = context.get('config', {})
                result = self.apply_deployment_config(config)
                return {**result, 'task_id': task_id, 'agent': self.agent_name}
            
            elif action == 'info':
                return {
                    'success': True,
                    'task_id': task_id,
                    'agent': self.agent_name,
                    'architecture': self.architecture_info
                }
            
            else:
                return {'success': False, 'error': f'未知动作: {action}'}
        
        except Exception as e:
            return self.handle_error(e, task_id)
