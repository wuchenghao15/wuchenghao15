# -*- coding: utf-8 -*-
"""
AI规则分析器 - MTSCOS AI项目
自动分析代码库中的常见问题模式，生成规则改进建议
"""

import os
import re
import ast
from typing import List, Dict, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RuleAnalyzer:
    """规则分析器"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.app_dir = os.path.join(self.project_root, 'app')
        self.rules_dir = os.path.join(self.project_root, '.trae', 'rules')
    
    def analyze_schema_compatibility(self) -> List[Dict]:
        """分析数据库Schema兼容性问题"""
        issues = []
        models_dir = os.path.join(self.app_dir, 'models')
        
        if not os.path.exists(models_dir):
            return issues
        
        for filename in os.listdir(models_dir):
            if not filename.endswith('.py'):
                continue
            
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name) and target.id == 'TABLE_NAME':
                                        table_name = None
                                        if isinstance(item.value, ast.Constant):
                                            table_name = item.value.value
                                        elif isinstance(item.value, ast.Str):
                                            table_name = item.value.s
                                        
                                        if table_name:
                                            insert_patterns = re.findall(
                                                r"INSERT INTO\s+[\w`'\"]+", content, re.IGNORECASE
                                            )
                                            for pattern in insert_patterns:
                                                if table_name.lower() in pattern.lower():
                                                    issues.append({
                                                        'type': 'schema_compatibility',
                                                        'file': filename,
                                                        'table': table_name,
                                                        'issue': f'INSERT语句可能与实际表结构不匹配',
                                                        'severity': 'medium'
                                                    })
            except Exception as e:
                logger.warning(f"分析模型文件失败 {filename}: {e}")
        
        return issues
    
    def analyze_blueprint_conflicts(self) -> List[Dict]:
        """分析蓝图注册冲突"""
        issues = []
        blueprints = {}
        
        routes_dir = os.path.join(self.app_dir, 'routes')
        api_dir = os.path.join(self.app_dir, 'api')
        
        for dir_path in [routes_dir, api_dir]:
            if not os.path.exists(dir_path):
                continue
            
            for filename in os.listdir(dir_path):
                if not filename.endswith('.py') or filename == '__init__.py':
                    continue
                
                filepath = os.path.join(dir_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                pattern = r"Blueprint\(['\"]([\w_]+)['\"]"
                matches = re.findall(pattern, content)
                
                for bp_name in matches:
                    if bp_name in blueprints:
                        issues.append({
                            'type': 'blueprint_conflict',
                            'file': filename,
                            'blueprint': bp_name,
                            'existing_file': blueprints[bp_name],
                            'issue': f'蓝图名称 "{bp_name}" 重复定义',
                            'severity': 'high'
                        })
                    else:
                        blueprints[bp_name] = filename
        
        return issues
    
    def analyze_template_context(self) -> List[Dict]:
        """分析模板上下文变量缺失"""
        issues = []
        templates_dir = os.path.join(self.project_root, 'templates', 'admin_app')
        
        if not os.path.exists(templates_dir):
            return issues
        
        base_file = os.path.join(templates_dir, 'base.html')
        if os.path.exists(base_file):
            with open(base_file, 'r', encoding='utf-8') as f:
                base_content = f.read()
            
            context_vars = re.findall(r"{{\s*(\w+)\s*}}", base_content)
            
            for filename in os.listdir(templates_dir):
                if not filename.endswith('.html') or filename == 'base.html':
                    continue
                
                template_name = filename.replace('.html', '')
                route_pattern = f"def admin_app_{template_name}"
                
                app_py_path = os.path.join(self.project_root, 'app.py')
                with open(app_py_path, 'r', encoding='utf-8') as f:
                    app_content = f.read()
                
                route_match = re.search(route_pattern, app_content)
                if route_match:
                    start = route_match.start()
                    end = app_content.find('return render_template', start)
                    if end > 0:
                        render_line = app_content[end:end+200]
                        missing_vars = []
                        for var in context_vars:
                            if var not in render_line and var != 'current_page':
                                missing_vars.append(var)
                        
                        if missing_vars:
                            issues.append({
                                'type': 'template_context',
                                'file': filename,
                                'route': f'/admin_app/{template_name}',
                                'missing_vars': missing_vars,
                                'issue': f'缺少模板上下文变量: {", ".join(missing_vars)}',
                                'severity': 'high'
                            })
        
        return issues
    
    def analyze_api_response_imports(self) -> List[Dict]:
        """分析API响应类导入问题"""
        issues = []
        api_response_path = os.path.join(self.app_dir, 'utils', 'api_response.py')
        
        with open(api_response_path, 'r', encoding='utf-8') as f:
            response_content = f.read()
        
        has_api_response_class = 'class APIResponse' in response_content
        
        routes_dir = os.path.join(self.app_dir, 'routes')
        api_dir = os.path.join(self.app_dir, 'api')
        
        for dir_path in [routes_dir, api_dir]:
            if not os.path.exists(dir_path):
                continue
            
            for filename in os.listdir(dir_path):
                if not filename.endswith('.py') or filename == '__init__.py':
                    continue
                
                filepath = os.path.join(dir_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'from app.utils.api_response import APIResponse' in content:
                    if not has_api_response_class:
                        issues.append({
                            'type': 'api_response_import',
                            'file': filename,
                            'issue': '导入了APIResponse类但该类不存在',
                            'severity': 'critical'
                        })
        
        return issues
    
    def analyze_frontend_api_calls(self) -> List[Dict]:
        """分析前后端API调用对齐问题"""
        issues = []
        templates_dir = os.path.join(self.project_root, 'templates', 'admin_app')
        
        if not os.path.exists(templates_dir):
            return issues
        
        api_endpoints = set()
        routes_dir = os.path.join(self.app_dir, 'routes')
        api_dir = os.path.join(self.app_dir, 'api')
        
        for dir_path in [routes_dir, api_dir]:
            if not os.path.exists(dir_path):
                continue
            
            for filename in os.listdir(dir_path):
                if not filename.endswith('.py') or filename == '__init__.py':
                    continue
                
                filepath = os.path.join(dir_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                patterns = re.findall(r"route\(['\"](/api[\w/\-]+)['\"]", content)
                api_endpoints.update(patterns)
        
        for filename in os.listdir(templates_dir):
            if not filename.endswith('.html'):
                continue
            
            filepath = os.path.join(templates_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontend_calls = re.findall(r"fetch\(['\"](/api[\w/\-]+)[?'\"]", content)
            
            for call in frontend_calls:
                if call not in api_endpoints:
                    issues.append({
                        'type': 'api_contract_mismatch',
                        'file': filename,
                        'endpoint': call,
                        'issue': f'前端调用的API端点不存在: {call}',
                        'severity': 'high'
                    })
        
        return issues
    
    def generate_rule_recommendations(self) -> Dict:
        """生成规则改进建议"""
        all_issues = []
        all_issues.extend(self.analyze_schema_compatibility())
        all_issues.extend(self.analyze_blueprint_conflicts())
        all_issues.extend(self.analyze_template_context())
        all_issues.extend(self.analyze_api_response_imports())
        all_issues.extend(self.analyze_frontend_api_calls())
        
        recommendations = {
            'total_issues': len(all_issues),
            'by_severity': {
                'critical': [i for i in all_issues if i['severity'] == 'critical'],
                'high': [i for i in all_issues if i['severity'] == 'high'],
                'medium': [i for i in all_issues if i['severity'] == 'medium'],
                'low': [i for i in all_issues if i['severity'] == 'low']
            },
            'rule_updates': []
        }
        
        schema_issues = [i for i in all_issues if i['type'] == 'schema_compatibility']
        if schema_issues:
            recommendations['rule_updates'].append({
                'chapter': '17. 数据库Schema兼容性规范',
                'reason': f'发现{len(schema_issues)}个Schema兼容性问题',
                'recommendations': [
                    '所有模型必须提供Schema迁移脚本',
                    '模型创建表时必须检测并兼容已有表结构',
                    '字段名变更必须向后兼容',
                    '提供字段映射机制处理新旧字段名'
                ]
            })
        
        blueprint_issues = [i for i in all_issues if i['type'] == 'blueprint_conflict']
        if blueprint_issues:
            recommendations['rule_updates'].append({
                'chapter': '18. 蓝图注册与冲突检测规范',
                'reason': f'发现{len(blueprint_issues)}个蓝图冲突问题',
                'recommendations': [
                    '蓝图名称必须全局唯一',
                    '注册前必须检测冲突',
                    '提供蓝图命名规范和命名空间',
                    '使用统一的蓝图注册中心'
                ]
            })
        
        context_issues = [i for i in all_issues if i['type'] == 'template_context']
        if context_issues:
            recommendations['rule_updates'].append({
                'chapter': '19. 模板上下文规范',
                'reason': f'发现{len(context_issues)}个模板上下文缺失问题',
                'recommendations': [
                    '定义所有admin_app页面必须传递的通用上下文变量清单',
                    '提供上下文生成辅助函数',
                    '模板继承链中变量必须传递',
                    '建立上下文变量依赖关系文档'
                ]
            })
        
        api_response_issues = [i for i in all_issues if i['type'] == 'api_response_import']
        if api_response_issues:
            recommendations['rule_updates'].append({
                'chapter': '20. API响应规范',
                'reason': f'发现{len(api_response_issues)}个API响应类导入问题',
                'recommendations': [
                    '统一API响应工具类必须提供',
                    '所有API模块必须使用统一的响应格式',
                    '响应类变更必须同步更新所有引用',
                    '提供响应格式兼容性层'
                ]
            })
        
        contract_issues = [i for i in all_issues if i['type'] == 'api_contract_mismatch']
        if contract_issues:
            recommendations['rule_updates'].append({
                'chapter': '21. API契约与前后端对齐规范',
                'reason': f'发现{len(contract_issues)}个API契约不匹配问题',
                'recommendations': [
                    '前后端字段名必须一致',
                    'API变更必须同步更新前端模板',
                    '提供API契约文档管理机制',
                    '建立前端API调用清单与后端API的映射关系'
                ]
            })
        
        return recommendations
    
    def run_analysis(self) -> None:
        """运行完整分析"""
        logger.info("[规则分析器] 开始分析代码库...")
        recommendations = self.generate_rule_recommendations()
        
        logger.info(f"[规则分析器] 共发现 {recommendations['total_issues']} 个问题")
        for severity, issues in recommendations['by_severity'].items():
            if issues:
                logger.info(f"  {severity.upper()}: {len(issues)} 个")
        
        if recommendations['rule_updates']:
            logger.info("[规则分析器] 建议新增规则章节:")
            for update in recommendations['rule_updates']:
                logger.info(f"  - {update['chapter']}")
                for rec in update['recommendations']:
                    logger.info(f"    * {rec}")
        
        logger.info("[规则分析器] 分析完成")
