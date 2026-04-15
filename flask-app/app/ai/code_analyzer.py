import os
import ast
import json
import re
import time
from app.utils.logging import logger
from app.config import Config

class AICodeAnalyzer:
    """AI代码分析器，用于分析项目代码并生成补充功能"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.analyzed_files = []
        self.code_patterns = {
            'flask_route': re.compile(r'@\w+\.route\(([^)]+)\)'),
            'class_def': re.compile(r'class\s+(\w+)\s*\('),
            'function_def': re.compile(r'def\s+(\w+)\s*\('),
            'import_statement': re.compile(r'^(import|from)\s+')
        }
        
    def analyze_project(self):
        """分析整个项目结构和代码"""
        logger.info("开始分析项目结构和代码")
        
        # 分析项目目录结构
        project_structure = self._analyze_directory_structure()
        
        # 分析关键文件
        key_files = self._get_key_files()
        file_analyses = []
        
        for file_path in key_files:
            file_analysis = self._analyze_file(file_path)
            file_analyses.append(file_analysis)
        
        # 生成项目分析报告
        analysis_report = {
            'timestamp': time.time(),
            'project_root': self.project_root,
            'project_structure': project_structure,
            'analyzed_files': file_analyses,
            'missing_features': self._identify_missing_features(file_analyses),
            'optimization_suggestions': self._generate_optimization_suggestions(file_analyses)
        }
        
        logger.info("项目分析完成")
        return analysis_report
    
    def _analyze_directory_structure(self):
        """分析项目目录结构"""
        structure = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # 跳过某些目录
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'env', '.idea', 'node_modules']]
            
            # 构建相对路径
            relative_path = os.path.relpath(root, self.project_root)
            if relative_path == '.':
                relative_path = ''
            
            # 只分析Python文件
            python_files = [f for f in files if f.endswith('.py')]
            
            if python_files:
                structure[relative_path] = python_files
        
        return structure
    
    def _get_key_files(self):
        """获取项目中的关键文件"""
        key_files = []
        
        # 主要应用文件
        main_files = ['app.py', '__init__.py']
        
        # 遍历目录，找到关键文件
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.py') and (file in main_files or 'views' in file or 'models' in file or 'utils' in file):
                    key_files.append(os.path.join(root, file))
        
        return key_files
    
    def _analyze_file(self, file_path):
        """分析单个文件"""
        logger.debug(f"分析文件: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分析文件内容
            relative_path = os.path.relpath(file_path, self.project_root)
            
            analysis = {
                'file_path': relative_path,
                'size': len(content),
                'lines': len(content.split('\n')),
                'imports': self._extract_imports(content),
                'classes': self._extract_classes(content),
                'functions': self._extract_functions(content),
                'routes': self._extract_routes(content),
                'patterns': self._extract_patterns(content)
            }
            
            self.analyzed_files.append(analysis)
            return analysis
            
        except Exception as e:
            logger.error(f"分析文件 {file_path} 时出错: {str(e)}")
            return {
                'file_path': file_path,
                'error': str(e)
            }
    
    def _extract_imports(self, content):
        """提取文件中的导入语句"""
        imports = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return imports
    
    def _extract_classes(self, content):
        """提取文件中的类定义"""
        classes = []
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                    'methods': []
                }
                
                # 提取类中的方法
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info['methods'].append({
                            'name': item.name,
                            'line': item.lineno,
                            'args': [arg.arg for arg in item.args.args]
                        })
                
                classes.append(class_info)
        
        return classes
    
    def _extract_functions(self, content):
        """提取文件中的函数定义"""
        functions = []
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查是否为类方法
                is_method = False
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        for item in parent.body:
                            if isinstance(item, ast.FunctionDef) and item.name == node.name and item.lineno == node.lineno:
                                is_method = True
                                break
                    if is_method:
                        break
                
                if not is_method:
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args]
                    })
        
        return functions
    
    def _extract_routes(self, content):
        """提取文件中的Flask路由"""
        routes = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            match = self.code_patterns['flask_route'].search(line)
            if match:
                # 获取路由装饰器的下一行函数定义
                for j in range(i+1, len(lines)):
                    func_line = lines[j].strip()
                    if func_line.startswith('def '):
                        func_match = self.code_patterns['function_def'].search(func_line)
                        if func_match:
                            routes.append({
                                'route': match.group(1),
                                'function': func_match.group(1),
                                'line': i + 1
                            })
                        break
        
        return routes
    
    def _extract_patterns(self, content):
        """提取文件中的代码模式"""
        patterns = {
            'has_database': 'db' in content or 'sql' in content.lower(),
            'has_authentication': 'auth' in content.lower() or 'login' in content.lower(),
            'has_logging': 'logger' in content or 'log' in content.lower(),
            'has_error_handling': 'try' in content or 'except' in content
        }
        
        return patterns
    
    def _identify_missing_features(self, file_analyses):
        """识别项目中缺失的功能"""
        missing_features = []
        
        # 检查是否有完善的测试机制
        has_tests = any('test' in file_analysis['file_path'].lower() for file_analysis in file_analyses)
        if not has_tests:
            missing_features.append({
                'type': 'testing',
                'description': '缺少完善的测试机制',
                'priority': 'high',
                'suggestion': '创建tests目录并添加单元测试和集成测试'
            })
        
        # 检查是否有CI/CD配置
        has_ci = any('.github' in dir_name for dir_name in os.listdir(self.project_root))
        if not has_ci:
            missing_features.append({
                'type': 'ci_cd',
                'description': '缺少CI/CD配置',
                'priority': 'medium',
                'suggestion': '添加GitHub Actions或GitLab CI配置，实现自动化测试和部署'
            })
        
        # 检查是否有API文档
        has_api_docs = any('docs' in dir_name for dir_name in os.listdir(self.project_root))
        if not has_api_docs:
            missing_features.append({
                'type': 'documentation',
                'description': '缺少API文档',
                'priority': 'medium',
                'suggestion': '使用Swagger或Redoc生成API文档'
            })
        
        # 检查是否有完整的错误处理
        all_content = '\n'.join([open(os.path.join(self.project_root, fa['file_path']), 'r').read() for fa in file_analyses if 'error' not in fa])
        has_comprehensive_error_handling = 'try' in all_content and 'except' in all_content and 'logger.error' in all_content
        if not has_comprehensive_error_handling:
            missing_features.append({
                'type': 'error_handling',
                'description': '缺少完整的错误处理机制',
                'priority': 'high',
                'suggestion': '添加统一的错误处理装饰器和异常类'
            })
        
        # 检查是否有数据验证
        has_data_validation = 'validate' in all_content.lower() or 'schema' in all_content.lower()
        if not has_data_validation:
            missing_features.append({
                'type': 'data_validation',
                'description': '缺少数据验证机制',
                'priority': 'high',
                'suggestion': '使用Marshmallow或WTForms添加数据验证'
            })
        
        return missing_features
    
    def _generate_optimization_suggestions(self, file_analyses):
        """生成代码优化建议"""
        suggestions = []
        
        # 检查重复代码模式
        route_count = 0
        for fa in file_analyses:
            if 'routes' in fa:
                route_count += len(fa['routes'])
        
        if route_count > 10:
            suggestions.append({
                'type': 'code_organization',
                'description': '路由数量较多，建议按功能模块化',
                'priority': 'medium',
                'suggestion': '将相关路由组织到不同的蓝图中'
            })
        
        # 检查是否有未使用的导入
        for file_analysis in file_analyses:
            if 'imports' in file_analysis and len(file_analysis['imports']) > 10:
                suggestions.append({
                    'type': 'code_cleanup',
                    'description': f'文件 {file_analysis["file_path"]} 导入语句较多，可能存在未使用的导入',
                    'priority': 'low',
                    'suggestion': '使用工具检查并移除未使用的导入'
                })
                break
        
        return suggestions
    
    def generate_missing_code(self, missing_feature):
        """根据缺失功能生成相应的代码"""
        feature_type = missing_feature['type']
        
        if feature_type == 'testing':
            return self._generate_test_code()
        elif feature_type == 'error_handling':
            return self._generate_error_handling_code()
        elif feature_type == 'data_validation':
            return self._generate_data_validation_code()
        elif feature_type == 'documentation':
            return self._generate_documentation_code()
        
        return None
    
    def _generate_test_code(self):
        """生成测试代码"""
        test_code = {
            'directory': 'tests',
            'files': [
                {
                    'name': '__init__.py',
                    'content': '# Test package\n'
                },
                {
                    'name': 'test_auth.py',
                    'content': '''import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login(client):
    """测试登录功能"""
    response = client.post('/auth/login', data=dict(
        username='test',
        password='test123'
    ), follow_redirects=True)
    assert b'登录成功' in response.data

def test_logout(client):
    """测试登出功能"""
    response = client.get('/auth/logout', follow_redirects=True)
    assert b'登出成功' in response.data
'''
                },
                {
                    'name': 'conftest.py',
                    'content': '''import pytest
from app import app
from app.models.user import User

@pytest.fixture(scope='session')
def app_fixture():
    """创建测试应用实例"""
    app.config.update({
        'TESTING': True,
        'DATABASE_PATH': 'test.db'
    })
    yield app

@pytest.fixture
def client(app_fixture):
    """创建测试客户端"""
    with app_fixture.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def setup_database():
    """设置测试数据库"""
    # 创建表
    User.create_table()
    yield
    # 清理数据库（如果需要）
'''
                }
            ]
        }
        
        return test_code
    
    def _generate_error_handling_code(self):
        """生成错误处理代码"""
        error_code = {
            'directory': 'app/utils',
            'files': [
                {
                    'name': 'error_handler.py',
                    'content': '''from flask import jsonify, render_template, request
from app.utils.logging import logger

class AppError(Exception):
    """应用程序自定义异常"""
    def __init__(self, message, status_code=500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def register_error_handlers(app):
    """注册全局错误处理器"""
    
    @app.errorhandler(AppError)
    def handle_app_error(error):
        """处理应用程序自定义异常"""
        logger.error(f"应用程序错误: {error.message} (状态码: {error.status_code})")
        
        # 如果是API请求，返回JSON响应
        if request.is_json:
            return jsonify({
                'success': False,
                'error': error.message,
                'status_code': error.status_code
            }), error.status_code
        
        # 否则返回HTML错误页面
        return render_template('error.html', error=error), error.status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        logger.warning("404错误: 页面未找到")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': '页面未找到',
                'status_code': 404
            }), 404
        
        return render_template('error.html', error=AppError('页面未找到', 404)), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        logger.error(f"500错误: {str(error)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': '服务器内部错误',
                'status_code': 500
            }), 500
        
        return render_template('error.html', error=AppError('服务器内部错误', 500)), 500
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """处理所有其他异常"""
        logger.error(f"未处理的异常: {str(error)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': '未知错误',
                'status_code': 500
            }), 500
        
        return render_template('error.html', error=AppError('未知错误', 500)), 500
'''
                }
            ]
        }
        
        return error_code
    
    def _generate_data_validation_code(self):
        """生成数据验证代码"""
        validation_code = {
            'directory': 'app/utils',
            'files': [
                {
                    'name': 'validation.py',
                    'content': '''from functools import wraps
from flask import request, jsonify
from app.utils.logging import logger

class Validator:
    """数据验证器"""
    
    @staticmethod
    def validate_required_fields(fields):
        """验证必填字段"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 获取请求数据
                if request.is_json:
                    data = request.get_json()
                else:
                    data = request.form.to_dict()
                
                # 检查必填字段
                missing_fields = [field for field in fields if field not in data or not data[field]]
                if missing_fields:
                    error_msg = f'缺少必填字段: {", ".join(missing_fields)}'
                    logger.warning(f"数据验证失败: {error_msg}")
                    
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': error_msg
                        }), 400
                    
                    from flask import flash, redirect, url_for
                    flash(error_msg, 'danger')
                    return redirect(url_for('auth.login'))
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def validate_email(email):
        """验证邮箱格式"""
        import re
        email_regex = r'^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$'
        return re.match(email_regex, email) is not None
    
    @staticmethod
    def validate_password_strength(password):
        """验证密码强度"""
        import re
        # 至少8个字符，包含大小写字母、数字和特殊字符
        return (
            len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'\d', password) and
            re.search(r'[^A-Za-z0-9]', password)
        )
'''
                }
            ]
        }
        
        return validation_code
    
    def _generate_documentation_code(self):
        """生成文档代码"""
        docs_code = {
            'directory': 'docs',
            'files': [
                {
                    'name': 'README.md',
                    'content': '''# MTSCOS AI Project

## 项目概述

MTSCOS AI Project 是一个基于Flask的AI应用框架，提供了AI实例管理、监控、学习等功能。

## 功能特性

- AI实例管理
- 自动错误监控和修复
- AI自我学习和优化
- 用户认证和授权
- 基于角色的访问控制
- 完善的日志记录

## 技术栈

- Python 3.8+
- Flask 2.0+
- SQLite
- HTML/CSS/JavaScript

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python app.py
```

应用将在 http://localhost:8888 启动。

## 项目结构

```
flask-app/
├── app.py              # 应用入口
├── app/                # 应用包
│   ├── __init__.py     # 应用初始化
│   ├── config.py       # 配置文件
│   ├── models/         # 数据模型
│   ├── views/          # 视图函数
│   ├── utils/          # 工具函数
│   └── ai/             # AI相关功能
├── templates/          # HTML模板
├── static/             # 静态资源
└── requirements.txt    # 依赖列表
```

## API文档

### 认证API

- `POST /auth/login` - 用户登录
- `GET /auth/logout` - 用户登出
- `POST /auth/register` - 用户注册

### AI API

- `GET /ai/instances` - 获取AI实例列表
- `POST /ai/create_instance` - 创建AI实例
- `GET /ai/delete_instance/<instance_id>` - 删除AI实例
- `GET /ai/bind_instance/<instance_id>/<user_id>` - 绑定AI实例到用户

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT
'''
                },
                {
                    'name': 'requirements.txt',
                    'content': '''Flask>=2.0.0
pytest>=7.0.0
requests>=2.26.0
python-dotenv>=0.19.0
'''
                }
            ]
        }
        
        return docs_code

# 初始化代码分析器实例
ai_code_analyzer = AICodeAnalyzer()
