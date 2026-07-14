# -*- coding: utf-8 -*-
import os
import ast
import re
import time
from app.utils.logging import logger
from app.config import Config


class AICodeAnalyzer:
    """AI代码分析器:用于分析项目代码并生成补充功能"""

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

        project_structure = self._analyze_directory_structure()

        key_files = self._get_key_files()
        file_analyses = []

        for file_path in key_files:
            file_analysis = self._analyze_file(file_path)
            file_analyses.append(file_analysis)

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
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'env', '.idea', 'node_modules']]

            relative_path = os.path.relpath(root, self.project_root)
            if relative_path == '.':
                relative_path = ''

            python_files = [f for f in files if f.endswith('.py')]

            if python_files:
                structure[relative_path] = python_files

        return structure

    def _get_key_files(self):
        """获取项目中的关键文件"""
        key_files = []

        main_files = ['app.py', '__init__.py']

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
            logger.error(f"分析文件失败: {file_path}, 错误: {str(e)}")
            return {}

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
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                        'methods': []
                    }

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info['methods'].append({
                                'name': item.name,
                                'line': item.lineno,
                                'args': [arg.arg for arg in item.args.args]
                            })

                    classes.append(class_info)
        except Exception as e:
            logger.error(f"提取类定义失败: {str(e)}")

        return classes

    def _extract_functions(self, content):
        """提取文件中的函数定义"""
        functions = []
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
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
        except Exception as e:
            logger.error(f"提取函数定义失败: {str(e)}")

        return functions

    def _extract_routes(self, content):
        """提取文件中的路由定义"""
        routes = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            match = self.code_patterns['flask_route'].search(line)
            if match:
                for j in range(i + 1, len(lines)):
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
            'has_logging': 'logger' in content or 'log' in content.lower(),
            'has_error_handling': 'try' in content or 'except' in content
        }
        return patterns

    def _identify_missing_features(self, file_analyses):
        """识别项目中缺失的功能"""
        missing_features = []

        has_tests = any('test' in file_analysis.get('file_path', '').lower() for file_analysis in file_analyses)
        if not has_tests:
            missing_features.append({
                'type': 'testing',
                'description': '缺少完善的测试机制',
                'priority': 'high',
                'suggestion': '创建tests目录并添加单元测试和集成测试'
            })

        try:
            has_ci = any('.github' in dir_name for dir_name in os.listdir(self.project_root))
        except Exception:
            has_ci = False
        if not has_ci:
            missing_features.append({
                'type': 'ci_cd',
                'description': '缺少CI/CD配置',
                'priority': 'medium',
                'suggestion': '添加GitHub Actions或GitLab CI配置,实现自动化测试和部署'
            })

        try:
            has_api_docs = any('docs' in dir_name for dir_name in os.listdir(self.project_root))
        except Exception:
            has_api_docs = False
        if not has_api_docs:
            missing_features.append({
                'type': 'documentation',
                'description': '缺少API文档',
                'priority': 'medium',
                'suggestion': '使用Swagger或Redoc生成API文档'
            })

        all_content = ''
        try:
            for fa in file_analyses:
                file_path = os.path.join(self.project_root, fa.get('file_path', ''))
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_content += f.read()
        except Exception:
            pass

        has_comprehensive_error_handling = 'try' in all_content and 'except' in all_content and 'logger.error' in all_content
        if not has_comprehensive_error_handling:
            missing_features.append({
                'type': 'error_handling',
                'description': '缺少完整的错误处理机制',
                'priority': 'high',
                'suggestion': '添加全局错误处理器和统一的错误日志记录'
            })

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

        route_count = 0
        for fa in file_analyses:
            if 'routes' in fa:
                route_count += len(fa.get('routes', []))

        if route_count > 20:
            suggestions.append({
                'type': 'code_organization',
                'description': '路由数量较多,建议按功能模块化',
                'priority': 'medium',
                'suggestion': '将相关路由组织到不同的蓝图中'
            })

        for file_analysis in file_analyses:
            if 'imports' in file_analysis and len(file_analysis.get('imports', [])) > 10:
                suggestions.append({
                    'type': 'code_cleanup',
                    'description': f'文件 {file_analysis.get("file_path", "")} 导入语句较多,可能存在未使用的导入',
                    'priority': 'low',
                    'suggestion': '使用工具检查并移除未使用的导入'
                })
                break

        return suggestions

    def generate_missing_code(self, missing_feature):
        """根据缺失功能生成相应的代码"""
        feature_type = missing_feature.get('type')

        if feature_type == 'testing':
            return self._generate_test_code()
        elif feature_type == 'error_handling':
            return self._generate_error_handling_code()
        elif feature_type == 'data_validation':
            return self._generate_data_validation_code()

        return None

    def _generate_test_code(self):
        """生成测试代码"""
        test_code = {
            'files': [
                {
                    'name': 'test_basic.py',
                    'content': '''import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
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
from app import create_app
from app.models.user import User

@pytest.fixture(scope='session')
def app_fixture():
    """创建测试应用实例"""
    app = create_app()
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
    User.create_table()
    yield
'''
                }
            ]
        }
        return test_code

    def _generate_error_handling_code(self):
        """生成错误处理代码"""
        error_code = {
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
        if request.is_json:
            return jsonify({
                'success': False,
                'error': error.message
            }), error.status_code
        return render_template('error.html', error=error), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        logger.warning("404错误: 页面未找到")
        if request.is_json:
            return jsonify({
                'success': False,
                'error': '页面未找到'
            }), 404
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        logger.error(f"500错误: {str(error)}")
        if request.is_json:
            return jsonify({
                'success': False,
                'error': '服务器内部错误'
            }), 500
        return render_template('500.html'), 500

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """处理所有其他异常"""
        logger.error(f"未处理的异常: {str(error)}")
        if request.is_json:
            return jsonify({
                'success': False,
                'error': '服务器错误'
            }), 500
        return render_template('error.html', error=error), 500
'''
                }
            ]
        }
        return error_code

    def _generate_data_validation_code(self):
        """生成数据验证代码"""
        validation_code = {
            'files': [
                {
                    'name': 'validation.py',
                    'content': '''from functools import wraps
from flask import request, jsonify
from app.utils.logging import logger
import logging

class Validator:
    """数据验证器"""

    @staticmethod
    def validate_required_fields(fields):
        """验证必填字段"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.is_json:
                    data = request.get_json()
                else:
                    data = request.form.to_dict()

                missing_fields = [field for field in fields if field not in data or not data[field]]
                if missing_fields:
                    error_msg = f'缺少必填字段: {", ".join(missing_fields)}'
                    logger.warning(f"数据验证失败: {error_msg}")
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    @staticmethod
    def validate_password_strength(password):
        """验证密码强度"""
        if len(password) < 8:
            return False, '密码长度至少8个字符'
        if not any(c.isupper() for c in password):
            return False, '密码必须包含大写字母'
        if not any(c.islower() for c in password):
            return False, '密码必须包含小写字母'
        if not any(c.isdigit() for c in password):
            return False, '密码必须包含数字'
        return True, '密码强度符合要求'
'''
                }
            ]
        }
        return validation_code
